"""LLM-based alert classification service (fixed version)."""
"""
import asyncio
import logging
import json
import re
import requests
from typing import Optional, Dict

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alert, Classification
from app.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

"""
"""
def classify_by_rules(alert: Alert) -> Dict[str, str]:
    """
#Fallback: rule-based classification if LLM fails.
"""
    severity = (alert.severity or '').lower()
    urgency = (alert.urgency or '').lower()
    event_type = (alert.event_type or '').lower()

    # High
    if any(w in severity for w in ['extreme', 'severe']):
        return {"criticality": "High", "rationale": "Severe severity level detected."}
    if any(w in urgency for w in ['immediate', 'warning']):
        return {"criticality": "High", "rationale": "Immediate urgency detected."}
    if 'earthquake' in event_type and 'moderate' not in severity:
        return {"criticality": "High", "rationale": "Earthquake event detected."}

    # Medium
    if any(w in severity for w in ['moderate', 'advisory']):
        return {"criticality": "Medium", "rationale": "Moderate severity."}
    if any(w in urgency for w in ['expected', 'watch', 'moderate']):
        return {"criticality": "Medium", "rationale": "Expected urgency level."}

    # Default
    return {"criticality": "Low", "rationale": "Low risk - monitoring only."}


async def classify_with_llm(alert: Alert) -> Optional[Dict[str, str]]:
    

    try:
        # Prepare prompt
        prompt = f""You are an emergency management AI assistant. Classify this alert's criticality as High, Medium, or Low.

Alert Details:
- Source: {alert.source}
- Event Type: {alert.event_type or 'N/A'}
- Severity: {alert.severity or 'N/A'}
- Urgency: {alert.urgency or 'N/A'}
- Title: {alert.title}
- Summary: {alert.summary[:200] if alert.summary else 'N/A'}
- Area: {alert.area or 'N/A'}

Respond ONLY with valid JSON like this:
{{"criticality": "High|Medium|Low", "rationale": "1-sentence explanation"}}
""

        url = f"{getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')}/api/generate"
        payload = {
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "options": {"temperature": 0.3}
        }

        # Run blocking request asynchronously
        response = await asyncio.to_thread(requests.post, url, json=payload, timeout=60)
        response.raise_for_status()

        content = response.json().get("response", "").strip()
        if not content:
            raise ValueError("Empty LLM response.")

        # Clean JSON if wrapped in code blocks
        content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
        result = json.loads(content)

        if result.get("criticality") not in ["High", "Medium", "Low"]:
            raise ValueError(f"Invalid criticality: {result}")

        logger.info(f"LLM classified alert {alert.id} as {result['criticality']}")
        return result

    except Exception as e:
        logger.warning(f"LLM classification failed: {e}")
        return None


async def classify_alert(alert: Alert, db: Session) -> Classification:
    """#Classify one alert via LLM or fallback rules.
"""
    result = await classify_with_llm(alert)
    model_version = settings.MODEL_NAME if result else "rules-fallback"

    if not result:
        result = classify_by_rules(alert)

    classification = Classification(
        alert_id=alert.id,
        criticality=result["criticality"],
        rationale=result.get("rationale", "")[:1000],
        model_version=model_version
    )
    db.add(classification)
    db.commit()
    db.refresh(classification)

    logger.info(f"Alert {alert.id} classified as {classification.criticality} using {model_version}.")
    return classification


async def classify_unclassified_alerts(limit: int = 10):
    """#Classify alerts that have no existing classification.
"""
    db = SessionLocal()
    try:
        unclassified = (
            db.query(Alert)
            .outerjoin(Classification)
            .filter(Classification.id == None)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )

        if not unclassified:
            logger.info("No unclassified alerts found.")
            return 0

        logger.info(f"Found {len(unclassified)} unclassified alerts.")
        count = 0
        for alert in unclassified:
            try:
                await classify_alert(alert, db)
                count += 1
            except Exception as e:
                logger.error(f"Failed to classify alert {alert.id}: {e}")

        logger.info(f"Classified {count} alerts.")
        return count
    finally:
        db.close()


async def classification_worker():
    """#Background worker to continuously classify alerts.
"""
    logger.info("=" * 60)
    logger.info("Alexandria EAS - Classification Worker Started")
    logger.info("=" * 60)
    logger.info(f"Model: {settings.MODEL_NAME}")

    while True:
        try:
            await classify_unclassified_alerts(limit=10)
        except Exception as e:
            logger.error(f"Classification worker error: {e}", exc_info=True)

        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(classification_worker())
"""
"""
LLM-based alert classification service (OpenAI API version)
"""
import os
from dotenv import load_dotenv

# Always load the .env file explicitly from backend directory
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
env_path = os.path.join(backend_root, ".env")
load_dotenv(dotenv_path=env_path)



import asyncio
import logging
import json
import re
import os
from typing import Optional, Dict
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))



import requests
from openai import OpenAI
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Alert, Classification
from app.settings import settings

# ---------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# OpenAI client initialization
# ---------------------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# ---------------------------------------------------------------------
# Rule-based fallback classifier
# ---------------------------------------------------------------------
def classify_by_rules(alert: Alert) -> Dict[str, str]:
    """Fallback rule-based classification when LLM is unavailable."""
    severity = (alert.severity or "").lower()
    urgency = (alert.urgency or "").lower()
    event_type = (alert.event_type or "").lower()

    # High priority
    if any(w in severity for w in ["extreme", "severe"]):
        return {"criticality": "High", "rationale": "Severe severity level detected."}
    if any(w in urgency for w in ["immediate", "warning"]):
        return {"criticality": "High", "rationale": "Immediate urgency detected."}
    if "earthquake" in event_type and "moderate" not in severity:
        return {"criticality": "High", "rationale": "Earthquake event detected."}

    # Medium priority
    if any(w in severity for w in ["moderate", "advisory"]):
        return {"criticality": "Medium", "rationale": "Moderate severity."}
    if any(w in urgency for w in ["expected", "watch", "moderate"]):
        return {"criticality": "Medium", "rationale": "Expected urgency level."}

    # Default Low
    return {"criticality": "Low", "rationale": "Low risk – monitoring only."}

# ---------------------------------------------------------------------
# OpenAI classification logic
# ---------------------------------------------------------------------
async def classify_with_llm(alert: Alert) -> Optional[Dict[str, str]]:
    """Classify an alert using OpenAI's GPT model."""
    try:
        prompt = f'''You are an emergency management AI assistant. Classify this alert's criticality as High, Medium, or Low.

Alert Details:
- Source: {alert.source}
- Event Type: {alert.event_type or 'N/A'}
- Severity: {alert.severity or 'N/A'}
- Urgency: {alert.urgency or 'N/A'}
- Title: {alert.title}
- Summary: {alert.summary[:200] if alert.summary else 'N/A'}
- Area: {alert.area or 'N/A'}

Respond ONLY with valid JSON like this:
{{"criticality": "High|Medium|Low", "rationale": "1-sentence explanation"}}
'''


        # Run the OpenAI call in a non-blocking way
        def call_openai():
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an alert classification assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content

        content = await asyncio.to_thread(call_openai)

        if not content:
            raise ValueError("Empty response from OpenAI API.")

        # Clean markdown/JSON formatting if necessary
        content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
        result = json.loads(content)

        if result.get("criticality") not in ["High", "Medium", "Low"]:
            raise ValueError(f"Invalid criticality: {result}")

        logger.info(f"LLM classified alert {alert.id} as {result['criticality']}")
        return result

    except Exception as e:
        logger.warning(f"OpenAI classification failed: {e}")
        return None

# ---------------------------------------------------------------------
# Database classification workflow
# ---------------------------------------------------------------------
async def classify_alert(alert: Alert, db: Session) -> Classification:
    """Classify one alert via OpenAI or fallback rules."""
    result = await classify_with_llm(alert)
    model_version = settings.MODEL_NAME if result else "rules-fallback"

    if not result:
        result = classify_by_rules(alert)

    classification = Classification(
        alert_id=alert.id,
        criticality=result["criticality"],
        rationale=result.get("rationale", "")[:1000],
        model_version=model_version,
    )

    db.add(classification)
    db.commit()
    db.refresh(classification)

    logger.info(f"Alert {alert.id} classified as {classification.criticality} using {model_version}.")
    return classification

# ---------------------------------------------------------------------
# Batch classification worker
# ---------------------------------------------------------------------
async def classify_unclassified_alerts(limit: int = 10):
    """Classify alerts without existing classifications."""
    db = SessionLocal()
    try:
        unclassified = (
            db.query(Alert)
            .outerjoin(Classification)
            .filter(Classification.id == None)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )

        if not unclassified:
            logger.info("No unclassified alerts found.")
            return 0

        logger.info(f"Found {len(unclassified)} unclassified alerts.")
        count = 0
        for alert in unclassified:
            try:
                await classify_alert(alert, db)
                count += 1
            except Exception as e:
                logger.error(f"Failed to classify alert {alert.id}: {e}")

        logger.info(f"Classified {count} alerts.")
        return count
    finally:
        db.close()

# ---------------------------------------------------------------------
# Continuous classification worker loop
# ---------------------------------------------------------------------
async def classification_worker():
    """Background worker to continuously classify alerts."""
    logger.info("=" * 60)
    logger.info("Alexandria EAS - OpenAI Classification Worker Started")
    logger.info("=" * 60)
    logger.info(f"Model: {settings.MODEL_NAME}")

    while True:
        try:
            await classify_unclassified_alerts(limit=10)
        except Exception as e:
            logger.error(f"Classification worker error: {e}", exc_info=True)

        await asyncio.sleep(30)  # Run every 30s

# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(classification_worker())
