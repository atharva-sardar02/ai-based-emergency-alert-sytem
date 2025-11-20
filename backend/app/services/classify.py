"""LLM-based alert classification service."""
import asyncio
import logging
import json
from typing import Optional, Dict
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alert, Classification
from app.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def classify_by_rules(alert: Alert) -> Dict[str, str]:
    """
    Rule-based classification fallback.
    Maps severity/urgency to criticality levels.
    """
    severity = (alert.severity or "").lower()
    urgency = (alert.urgency or "").lower()
    event_type = (alert.event_type or "").lower()
    
    # High criticality conditions
    if any(word in severity for word in ["extreme", "severe"]):
        return {
            "criticality": "High",
            "rationale": "Classified as High due to severe severity level."
        }
    
    if any(word in urgency for word in ["immediate", "warning"]):
        return {
            "criticality": "High",
            "rationale": "Classified as High due to immediate urgency."
        }
    
    if "earthquake" in event_type and alert.severity and "moderate" not in severity:
        return {
            "criticality": "High",
            "rationale": "Earthquake detected - classified as High priority."
        }
    
    # Medium criticality conditions
    if any(word in severity for word in ["moderate", "advisory"]):
        return {
            "criticality": "Medium",
            "rationale": "Classified as Medium due to moderate severity."
        }
    
    if any(word in urgency for word in ["expected", "watch", "moderate"]):
        return {
            "criticality": "Medium",
            "rationale": "Classified as Medium due to expected urgency level."
        }
    
    # Default to Low
    return {
        "criticality": "Low",
        "rationale": "Classified as Low - monitoring situation."
    }


async def classify_with_openai(alert: Alert) -> Optional[Dict[str, str]]:
    """
    Classify alert using OpenAI API.
    Returns None if OpenAI is unavailable or API key is missing.
    """
    # Check if API key is available
    if not settings.OPENAI_API_KEY:
        return None
    
    try:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            logger.warning("OpenAI library not available - skipping OpenAI classification")
            return None

        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

        # Build prompt (same format as Ollama)
        prompt = f"""You are an emergency management AI assistant. Classify this alert's criticality as High, Medium, or Low.

Alert Details:
- Source: {alert.source}
- Event Type: {alert.event_type or 'N/A'}
- Severity: {alert.severity or 'N/A'}
- Urgency: {alert.urgency or 'N/A'}
- Title: {alert.title}
- Summary: {alert.summary[:200] if alert.summary else 'N/A'}
- Area: {alert.area or 'N/A'}

Respond with a JSON object in this exact format:
{{"criticality": "High|Medium|Low", "rationale": "Brief 1-sentence explanation"}}"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}  # Request JSON response
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        if not content:
            raise ValueError("Empty response from OpenAI API")
        
        # Parse JSON
        result = json.loads(content)
        
        # Validate
        if result.get("criticality") not in ["High", "Medium", "Low"]:
            raise ValueError(f"Invalid criticality: {result.get('criticality')}")
        
        logger.info(f"OpenAI classified alert {alert.id} as {result['criticality']}")
        return result
        
    except Exception as e:
        logger.warning(
            "OpenAI classification failed (model=%s): %s - falling back to Ollama",
            settings.OPENAI_MODEL,
            e,
        )
        return None


async def classify_with_ollama(alert: Alert) -> Optional[Dict[str, str]]:
    """
    Classify alert using local LLM via Ollama.
    Returns None if LLM is unavailable.
    """
    try:
        # Use explicit client so we honor OLLAMA_BASE_URL from settings
        try:
            from ollama import Client  # type: ignore
        except Exception as e:
            logger.warning("Ollama library not available - using rule-based classification")
            return None

        client = Client(host=getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434'))

        # Build prompt
        prompt = f"""You are an emergency management AI assistant. Classify this alert's criticality as High, Medium, or Low.

Alert Details:
- Source: {alert.source}
- Event Type: {alert.event_type or 'N/A'}
- Severity: {alert.severity or 'N/A'}
- Urgency: {alert.urgency or 'N/A'}
- Title: {alert.title}
- Summary: {alert.summary[:200] if alert.summary else 'N/A'}
- Area: {alert.area or 'N/A'}

Respond ONLY with valid JSON in this format:
{{"criticality": "High|Medium|Low", "rationale": "Brief 1-sentence explanation"}}"""

        # Call Ollama
        response = client.chat(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3}
        )
        
        # Parse response
        content = response.get('message', {}).get('content', '').strip()
        if not content:
            raise ValueError("Empty response from Ollama chat API")
        
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        # Validate
        if result.get("criticality") not in ["High", "Medium", "Low"]:
            raise ValueError(f"Invalid criticality: {result.get('criticality')}")
        
        logger.info(f"LLM classified alert {alert.id} as {result['criticality']}")
        return result
        
    except Exception as e:
        logger.warning(
            "LLM classification failed via Ollama (host=%s, model=%s): %s - falling back to rules",
            getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434'),
            settings.MODEL_NAME,
            e,
        )
        return None


async def classify_alert(alert: Alert, db: Session) -> Classification:
    """
    Classify a single alert using three-tier fallback: OpenAI → Ollama → Rules.
    """
    result = None
    model_version = "rules-fallback"
    
    # Tier 1: Try OpenAI first (if API key available)
    if settings.OPENAI_API_KEY:
        result = await classify_with_openai(alert)
        if result:
            model_version = f"openai-{settings.OPENAI_MODEL}"
    
    # Tier 2: Try Ollama if OpenAI failed or unavailable
    if not result:
        result = await classify_with_ollama(alert)
        if result:
            model_version = settings.MODEL_NAME
    
    # Tier 3: Fallback to rules if both LLMs failed
    if not result:
        result = classify_by_rules(alert)
        model_version = "rules-fallback"
    
    # Create classification record
    classification = Classification(
        alert_id=alert.id,
        criticality=result["criticality"],
        rationale=result.get("rationale", "")[:1000],  # Truncate if needed
        model_version=model_version
    )
    
    db.add(classification)
    db.commit()
    db.refresh(classification)
    
    logger.info(f"Alert {alert.id} classified as {classification.criticality} by {model_version}")
    return classification


async def classify_unclassified_alerts(limit: int = 10):
    """
    Find unclassified alerts and classify them.
    """
    db = SessionLocal()
    try:
        # Find alerts without classification
        unclassified = db.query(Alert).outerjoin(Classification).filter(
            Classification.id == None
        ).order_by(Alert.created_at.desc()).limit(limit).all()
        
        if not unclassified:
            logger.info("No unclassified alerts found")
            return 0
        
        logger.info(f"Found {len(unclassified)} unclassified alerts")
        
        count = 0
        for alert in unclassified:
            try:
                await classify_alert(alert, db)
                count += 1
            except Exception as e:
                logger.error(f"Failed to classify alert {alert.id}: {e}")
        
        logger.info(f"Classified {count} alerts")
        return count
        
    finally:
        db.close()


async def classification_worker():
    """
    Continuous worker that classifies unclassified alerts.
    """
    logger.info("=" * 60)
    logger.info("Alexandria EAS - Classification Worker")
    logger.info("=" * 60)
    if settings.OPENAI_API_KEY:
        logger.info(f"Primary: OpenAI ({settings.OPENAI_MODEL})")
        logger.info(f"Fallback 1: Ollama ({settings.MODEL_NAME})")
    else:
        logger.info(f"Primary: Ollama ({settings.MODEL_NAME})")
    logger.info("Fallback 2: Rule-based classification")
    
    while True:
        try:
            await classify_unclassified_alerts(limit=10)
        except Exception as e:
            logger.error(f"Classification worker error: {e}", exc_info=True)
        
        # Wait before next check
        await asyncio.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    asyncio.run(classification_worker())

