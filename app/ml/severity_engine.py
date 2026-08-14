"""
severity_engine.py
-------------------
AI-powered symptom and vitals severity detection engine.

Severity levels:
  NORMAL → MILD → MODERATE → SEVERE → CRITICAL

Analyses:
  1. Vitals readings (BP, HR, glucose, SpO2, temperature)
  2. Symptom text (NLP keyword matching + severity scoring)
  3. Trend deterioration (compares to recent readings)
"""

from dataclasses import dataclass, field
from typing import Optional
import re

SEVERITY_NORMAL   = "normal"
SEVERITY_MILD     = "mild"
SEVERITY_MODERATE = "moderate"
SEVERITY_SEVERE   = "severe"
SEVERITY_CRITICAL = "critical"

SEVERITY_ORDER = {
    SEVERITY_NORMAL: 0, SEVERITY_MILD: 1,
    SEVERITY_MODERATE: 2, SEVERITY_SEVERE: 3, SEVERITY_CRITICAL: 4,
}
SEVERITY_COLORS = {
    SEVERITY_NORMAL: "🟢", SEVERITY_MILD: "🟡",
    SEVERITY_MODERATE: "🟠", SEVERITY_SEVERE: "🔴", SEVERITY_CRITICAL: "🚨",
}

@dataclass
class SeverityFlag:
    parameter: str
    value: str
    severity: str
    message: str
    recommendation: str

@dataclass
class SeverityReport:
    overall_severity: str
    flags: list = field(default_factory=list)
    symptom_score: float = 0.0
    vitals_score: float = 0.0
    trend_score: float = 0.0
    combined_score: float = 0.0
    should_alert_doctor: bool = False
    alert_subject: str = ""
    alert_body: str = ""

    @property
    def icon(self):
        return SEVERITY_COLORS.get(self.overall_severity, "⚪")

    @property
    def severe_flags(self):
        return [f for f in self.flags if SEVERITY_ORDER.get(f.severity, 0) >= SEVERITY_ORDER[SEVERITY_SEVERE]]

    @property
    def critical_flags(self):
        return [f for f in self.flags if f.severity == SEVERITY_CRITICAL]

SYMPTOM_RULES = [
    (r"chest\s*pain|chest\s*tightness|crushing\s*chest", SEVERITY_CRITICAL,
     "Patient reports chest pain — possible cardiac event",
     "🚨 Call patient immediately. Consider emergency services."),
    (r"difficulty\s*breath|can.t\s*breath|shortness\s*of\s*breath|\bsob\b", SEVERITY_CRITICAL,
     "Patient reports difficulty breathing — possible respiratory emergency",
     "🚨 Urgent assessment required. Consider emergency referral."),
    (r"stroke|face\s*drooping|arm\s*weakness|speech\s*difficult|sudden\s*numb", SEVERITY_CRITICAL,
     "Patient reports stroke-like symptoms",
     "🚨 EMERGENCY. Call emergency services immediately."),
    (r"unconscious|fainting|passed?\s*out|collaps", SEVERITY_CRITICAL,
     "Patient reports loss of consciousness or collapse",
     "🚨 EMERGENCY. Immediate medical attention required."),
    (r"severe\s*head|worst\s*head|thunderclap|sudden\s*head", SEVERITY_CRITICAL,
     "Sudden severe headache — possible subarachnoid haemorrhage",
     "🚨 Urgent assessment. Consider emergency CT scan referral."),
    (r"blood\s*in\s*urine|blood\s*in\s*stool|vomiting?\s*blood|coughing?\s*blood", SEVERITY_CRITICAL,
     "Patient reports internal bleeding symptoms",
     "🚨 Immediate medical attention required."),
    (r"severe\s*dizzin|extreme\s*dizzin|can.t\s*stand|can.t\s*walk", SEVERITY_SEVERE,
     "Patient reports severe dizziness affecting mobility",
     "📞 Contact patient within 2 hours. Assess fall risk."),
    (r"high\s*fever|fever\s*above\s*39|very\s*high\s*temp", SEVERITY_SEVERE,
     "Patient reports very high fever (>39°C)",
     "📞 Contact patient today. Urgent infection workup."),
    (r"blurr?ed?\s*vision|sudden\s*vision|vision\s*loss|can.t\s*see", SEVERITY_SEVERE,
     "Patient reports vision disturbance",
     "📞 Urgent review. Check blood pressure immediately."),
    (r"heart\s*racing|palpitat|heart\s*pounding|heart\s*beating\s*fast", SEVERITY_SEVERE,
     "Patient reports heart palpitations",
     "📞 ECG recommended. Contact patient today."),
    (r"numb(ness)?\s*(in|on)\s*(arm|leg|face|hand)|tingle|tingling", SEVERITY_SEVERE,
     "Patient reports numbness or tingling — possible neurological sign",
     "📞 Review within 24 hours. Consider neurological assessment."),
    (r"headache|head\s*ache|head\s*pain", SEVERITY_MODERATE,
     "Patient reports headache",
     "📋 Monitor. If persistent or worsening, escalate."),
    (r"dizz(y|iness)|lightheaded", SEVERITY_MODERATE,
     "Patient reports dizziness or lightheadedness",
     "📋 Check blood pressure readings. Follow up this week."),
    (r"swelling|swollen|edema|oedema", SEVERITY_MODERATE,
     "Patient reports swelling — possible fluid retention",
     "📋 Review medications. Check for signs of heart failure."),
    (r"fatigue|extreme\s*tired|very\s*tired|exhausted", SEVERITY_MODERATE,
     "Patient reports fatigue",
     "📋 Review recent vitals trends. Follow up this week."),
    (r"nausea|vomit|throw\s*up", SEVERITY_MODERATE,
     "Patient reports nausea or vomiting",
     "📋 Monitor hydration. Follow up within 48 hours."),
    (r"back\s*pain|joint\s*pain|muscle\s*pain|\bache\b", SEVERITY_MILD,
     "Patient reports pain",
     "📝 Note for next appointment."),
    (r"sleep|insomnia|can.t\s*sleep", SEVERITY_MILD,
     "Patient reports sleep difficulties",
     "📝 Note for next appointment."),
]

def _vitals_flags(v: dict) -> list:
    flags = []
    sbp = v.get("systolic_bp")
    if sbp:
        if sbp >= 180:
            flags.append(SeverityFlag("Systolic BP", f"{sbp} mmHg", SEVERITY_CRITICAL,
                f"Hypertensive crisis — systolic BP {sbp} mmHg (≥180)",
                "🚨 Emergency antihypertensive treatment required immediately."))
        elif sbp >= 160:
            flags.append(SeverityFlag("Systolic BP", f"{sbp} mmHg", SEVERITY_SEVERE,
                f"Severely elevated systolic BP {sbp} mmHg",
                "📞 Contact patient today. Review antihypertensive medication."))
        elif sbp >= 140:
            flags.append(SeverityFlag("Systolic BP", f"{sbp} mmHg", SEVERITY_MODERATE,
                f"Elevated systolic BP {sbp} mmHg (Stage 2 hypertension)",
                "📋 Review BP medications at next appointment."))
        elif sbp < 90:
            flags.append(SeverityFlag("Systolic BP", f"{sbp} mmHg", SEVERITY_SEVERE,
                f"Hypotension — systolic BP {sbp} mmHg (<90)",
                "📞 Contact patient. Assess for shock or dehydration."))
    dbp = v.get("diastolic_bp")
    if dbp:
        if dbp >= 120:
            flags.append(SeverityFlag("Diastolic BP", f"{dbp} mmHg", SEVERITY_CRITICAL,
                f"Hypertensive crisis — diastolic BP {dbp} mmHg",
                "🚨 Emergency treatment required immediately."))
        elif dbp >= 100:
            flags.append(SeverityFlag("Diastolic BP", f"{dbp} mmHg", SEVERITY_SEVERE,
                f"Severely elevated diastolic BP {dbp} mmHg",
                "📞 Contact patient today. Urgent medication review."))
        elif dbp >= 90:
            flags.append(SeverityFlag("Diastolic BP", f"{dbp} mmHg", SEVERITY_MODERATE,
                f"Elevated diastolic BP {dbp} mmHg",
                "📋 Review BP medications."))
    hr = v.get("heart_rate")
    if hr:
        if hr >= 150:
            flags.append(SeverityFlag("Heart Rate", f"{hr} bpm", SEVERITY_CRITICAL,
                f"Extreme tachycardia — {hr} bpm",
                "🚨 Possible cardiac arrhythmia. Emergency assessment."))
        elif hr >= 120:
            flags.append(SeverityFlag("Heart Rate", f"{hr} bpm", SEVERITY_SEVERE,
                f"Tachycardia — {hr} bpm",
                "📞 ECG recommended. Contact patient today."))
        elif hr >= 100:
            flags.append(SeverityFlag("Heart Rate", f"{hr} bpm", SEVERITY_MODERATE,
                f"Elevated heart rate — {hr} bpm",
                "📋 Monitor. Review at next appointment."))
        elif hr < 40:
            flags.append(SeverityFlag("Heart Rate", f"{hr} bpm", SEVERITY_CRITICAL,
                f"Extreme bradycardia — {hr} bpm",
                "🚨 Emergency cardiac assessment required."))
        elif hr < 60:
            flags.append(SeverityFlag("Heart Rate", f"{hr} bpm", SEVERITY_MILD,
                f"Low heart rate — {hr} bpm",
                "📝 Review medications (beta-blockers?)."))
    glucose = v.get("glucose_level")
    if glucose:
        g = float(glucose)
        if g >= 400:
            flags.append(SeverityFlag("Glucose", f"{g:.0f} mg/dL", SEVERITY_CRITICAL,
                f"Dangerously high glucose {g:.0f} mg/dL — possible DKA",
                "🚨 Emergency. Risk of diabetic ketoacidosis."))
        elif g >= 250:
            flags.append(SeverityFlag("Glucose", f"{g:.0f} mg/dL", SEVERITY_SEVERE,
                f"Very high glucose {g:.0f} mg/dL",
                "📞 Contact patient today. Review insulin/medication."))
        elif g >= 180:
            flags.append(SeverityFlag("Glucose", f"{g:.0f} mg/dL", SEVERITY_MODERATE,
                f"High glucose {g:.0f} mg/dL",
                "📋 Review diabetes management."))
        elif g < 54:
            flags.append(SeverityFlag("Glucose", f"{g:.0f} mg/dL", SEVERITY_CRITICAL,
                f"Severe hypoglycaemia — {g:.0f} mg/dL",
                "🚨 Emergency. Patient may be unconscious. Call immediately."))
        elif g < 70:
            flags.append(SeverityFlag("Glucose", f"{g:.0f} mg/dL", SEVERITY_SEVERE,
                f"Hypoglycaemia — {g:.0f} mg/dL",
                "📞 Contact patient immediately. Instruct to take sugar."))
    spo2 = v.get("oxygen_saturation")
    if spo2:
        if spo2 < 90:
            flags.append(SeverityFlag("SpO2", f"{spo2}%", SEVERITY_CRITICAL,
                f"Critically low oxygen saturation {spo2}% — hypoxia",
                "🚨 Emergency. Patient may need oxygen therapy immediately."))
        elif spo2 < 94:
            flags.append(SeverityFlag("SpO2", f"{spo2}%", SEVERITY_SEVERE,
                f"Low oxygen saturation {spo2}%",
                "📞 Contact patient urgently. Assess breathing."))
        elif spo2 < 96:
            flags.append(SeverityFlag("SpO2", f"{spo2}%", SEVERITY_MODERATE,
                f"Slightly reduced SpO2 {spo2}%",
                "📋 Monitor closely. Follow up within 48 hours."))
    temp = v.get("temperature_c")
    if temp:
        t = float(temp)
        if t >= 40.0:
            flags.append(SeverityFlag("Temperature", f"{t:.1f}°C", SEVERITY_CRITICAL,
                f"Dangerously high temperature {t:.1f}°C",
                "🚨 Emergency. Risk of seizure/organ damage."))
        elif t >= 39.0:
            flags.append(SeverityFlag("Temperature", f"{t:.1f}°C", SEVERITY_SEVERE,
                f"High fever {t:.1f}°C",
                "📞 Contact patient today. Consider infection workup."))
        elif t >= 37.5:
            flags.append(SeverityFlag("Temperature", f"{t:.1f}°C", SEVERITY_MODERATE,
                f"Mild fever {t:.1f}°C",
                "📋 Monitor. Follow up if persists."))
        elif t < 35.0:
            flags.append(SeverityFlag("Temperature", f"{t:.1f}°C", SEVERITY_SEVERE,
                f"Hypothermia — {t:.1f}°C",
                "📞 Contact patient immediately."))
    return flags


class SeverityEngine:

    def analyse(self, vitals: dict, symptoms: str = "",
                recent_history: list = None, patient_name: str = "Patient") -> SeverityReport:
        all_flags = []
        vitals_flags = _vitals_flags(vitals)
        all_flags.extend(vitals_flags)
        vitals_score = self._score(vitals_flags)
        symptom_flags = self._symptom_flags(symptoms)
        all_flags.extend(symptom_flags)
        symptom_score = self._score(symptom_flags)
        trend_flags = self._trend_flags(recent_history or [], vitals)
        all_flags.extend(trend_flags)
        trend_score = self._score(trend_flags)
        combined = (vitals_score * 0.5) + (symptom_score * 0.35) + (trend_score * 0.15)
        if all_flags:
            overall = max(all_flags, key=lambda f: SEVERITY_ORDER.get(f.severity, 0)).severity
        else:
            overall = SEVERITY_NORMAL
        should_alert = SEVERITY_ORDER.get(overall, 0) >= SEVERITY_ORDER[SEVERITY_MODERATE]
        subject, body = self._build_alert(patient_name, overall, all_flags, vitals, symptoms)
        return SeverityReport(
            overall_severity=overall,
            flags=sorted(all_flags, key=lambda f: -SEVERITY_ORDER.get(f.severity, 0)),
            symptom_score=round(symptom_score, 3),
            vitals_score=round(vitals_score, 3),
            trend_score=round(trend_score, 3),
            combined_score=round(combined, 3),
            should_alert_doctor=should_alert,
            alert_subject=subject,
            alert_body=body,
        )

    def _symptom_flags(self, text: str) -> list:
        if not text or not text.strip():
            return []
        text_lower = text.lower()
        flags = []
        seen = set()
        for pattern, severity, message, recommendation in SYMPTOM_RULES:
            if pattern not in seen and re.search(pattern, text_lower):
                seen.add(pattern)
                match = re.search(pattern, text_lower)
                flags.append(SeverityFlag(
                    "Symptom", match.group(0) if match else "reported",
                    severity, message, recommendation))
        return flags

    def _trend_flags(self, history: list, current: dict) -> list:
        flags = []
        if len(history) < 2:
            return flags
        try:
            recent = history[-3:] if len(history) >= 3 else history
            sbp_vals = [r.systolic_bp for r in recent if r.systolic_bp]
            if sbp_vals and current.get("systolic_bp"):
                avg = sum(sbp_vals) / len(sbp_vals)
                change = current["systolic_bp"] - avg
                if change >= 30:
                    flags.append(SeverityFlag("BP Trend", f"+{change:.0f} mmHg",
                        SEVERITY_SEVERE,
                        f"Systolic BP has risen sharply +{change:.0f} mmHg vs recent avg {avg:.0f} mmHg",
                        "📞 BP is deteriorating. Review medication urgently."))
                elif change >= 15:
                    flags.append(SeverityFlag("BP Trend", f"+{change:.0f} mmHg",
                        SEVERITY_MODERATE,
                        f"Systolic BP trending upward +{change:.0f} mmHg",
                        "📋 Monitor BP trend closely."))
            hr_vals = [r.heart_rate for r in recent if r.heart_rate]
            if hr_vals and current.get("heart_rate"):
                avg = sum(hr_vals) / len(hr_vals)
                change = current["heart_rate"] - avg
                if change >= 30:
                    flags.append(SeverityFlag("Heart Rate Trend", f"+{change:.0f} bpm",
                        SEVERITY_SEVERE,
                        f"Heart rate jumped +{change:.0f} bpm vs recent avg {avg:.0f} bpm",
                        "📞 Assess for arrhythmia or cardiac stress."))
            g_vals = [float(r.glucose_level) for r in recent if r.glucose_level]
            if g_vals and current.get("glucose_level"):
                avg = sum(g_vals) / len(g_vals)
                change = float(current["glucose_level"]) - avg
                if change >= 100:
                    flags.append(SeverityFlag("Glucose Trend", f"+{change:.0f} mg/dL",
                        SEVERITY_SEVERE,
                        f"Glucose risen sharply +{change:.0f} mg/dL vs avg {avg:.0f} mg/dL",
                        "📞 Review diabetes management urgently."))
        except Exception:
            pass
        return flags

    @staticmethod
    def _score(flags: list) -> float:
        if not flags:
            return 0.0
        score_map = {SEVERITY_NORMAL: 0.0, SEVERITY_MILD: 0.2,
                     SEVERITY_MODERATE: 0.5, SEVERITY_SEVERE: 0.75, SEVERITY_CRITICAL: 1.0}
        scores = [score_map.get(f.severity, 0.0) for f in flags]
        return min(1.0, sum(scores) / max(len(scores), 1) + max(scores) * 0.3)

    @staticmethod
    def _build_alert(patient_name, overall, flags, vitals, symptoms):
        icon = SEVERITY_COLORS.get(overall, "⚪")
        subject = f"{icon} {overall.upper()} SEVERITY ALERT — {patient_name}"
        lines = [f"{icon} PATIENT SEVERITY ALERT — {overall.upper()}",
                 "=" * 50, f"Patient: {patient_name}",
                 f"Overall Severity: {overall.upper()}", ""]
        crit = [f for f in flags if f.severity == SEVERITY_CRITICAL]
        sev = [f for f in flags if f.severity == SEVERITY_SEVERE]
        if crit:
            lines.append("🚨 CRITICAL FINDINGS:")
            for f in crit:
                lines.append(f"  • {f.parameter} ({f.value}): {f.message}")
                lines.append(f"    → {f.recommendation}")
            lines.append("")
        if sev:
            lines.append("🔴 SEVERE FINDINGS:")
            for f in sev:
                lines.append(f"  • {f.parameter} ({f.value}): {f.message}")
                lines.append(f"    → {f.recommendation}")
            lines.append("")
        lines.append("📊 CURRENT VITALS:")
        if vitals.get("systolic_bp") and vitals.get("diastolic_bp"):
            lines.append(f"  Blood Pressure: {vitals['systolic_bp']}/{vitals['diastolic_bp']} mmHg")
        if vitals.get("heart_rate"):
            lines.append(f"  Heart Rate: {vitals['heart_rate']} bpm")
        if vitals.get("glucose_level"):
            lines.append(f"  Glucose: {float(vitals['glucose_level']):.0f} mg/dL")
        if vitals.get("oxygen_saturation"):
            lines.append(f"  SpO2: {vitals['oxygen_saturation']}%")
        if vitals.get("temperature_c"):
            lines.append(f"  Temperature: {float(vitals['temperature_c']):.1f}°C")
        if symptoms:
            lines += ["", "🩺 REPORTED SYMPTOMS:", f"  {symptoms}"]
        lines += ["", "=" * 50, "Please review this patient immediately."]
        return subject, "\n".join(lines)
