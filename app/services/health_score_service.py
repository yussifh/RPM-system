"""
health_score_service.py
-----------------------
Calculates a composite health score (0-100) based on vitals,
medications, lifestyle, and AI risk predictions.
"""


class HealthScoreService:

    # Weight factors for the composite score
    WEIGHTS = {
        "bp":          0.25,
        "hr":          0.10,
        "glucose":     0.20,
        "spo2":        0.15,
        "temp":        0.05,
        "bmi":         0.10,
        "adherence":   0.10,
        "risk":        0.05,
    }

    def calculate(self, vitals=None, bmi=None, adherence=None,
                  latest_risk_scores=None) -> dict:
        """
        Calculate a composite health score.
        Returns dict with score (0-100), grade, breakdown, and recommendations.
        """
        scores = {}
        recommendations = []

        # Blood Pressure Score (0-100)
        if vitals and vitals.systolic_bp and vitals.diastolic_bp:
            sbp = vitals.systolic_bp
            dbp = vitals.diastolic_bp
            if sbp < 120 and dbp < 80:
                scores["bp"] = 100
            elif sbp < 130 and dbp < 85:
                scores["bp"] = 85
            elif sbp < 140 and dbp < 90:
                scores["bp"] = 65
                recommendations.append("Blood pressure is elevated. Monitor closely.")
            elif sbp < 160 and dbp < 100:
                scores["bp"] = 40
                recommendations.append("High blood pressure detected. Consult your doctor.")
            else:
                scores["bp"] = 20
                recommendations.append("⚠️ Severe hypertension. Seek medical attention.")

        # Heart Rate Score
        if vitals and vitals.heart_rate:
            hr = vitals.heart_rate
            if 60 <= hr <= 80:
                scores["hr"] = 100
            elif 50 <= hr <= 100:
                scores["hr"] = 80
            elif 45 <= hr <= 110:
                scores["hr"] = 55
                recommendations.append("Heart rate outside normal resting range.")
            else:
                scores["hr"] = 30
                recommendations.append("Abnormal heart rate detected.")

        # Glucose Score
        if vitals and vitals.glucose_level:
            glucose = float(vitals.glucose_level)
            if 70 <= glucose <= 120:
                scores["glucose"] = 100
            elif 70 <= glucose <= 140:
                scores["glucose"] = 80
            elif glucose < 70:
                scores["glucose"] = 45
                recommendations.append("Low glucose level. Eat a snack.")
            elif glucose <= 180:
                scores["glucose"] = 50
                recommendations.append("Elevated glucose level.")
            else:
                scores["glucose"] = 25
                recommendations.append("⚠️ Very high glucose level. Contact your doctor.")

        # SpO2 Score
        if vitals and vitals.oxygen_saturation:
            spo2 = vitals.oxygen_saturation
            if spo2 >= 97:
                scores["spo2"] = 100
            elif spo2 >= 95:
                scores["spo2"] = 85
            elif spo2 >= 92:
                scores["spo2"] = 55
                recommendations.append("Oxygen saturation is low. Monitor breathing.")
            else:
                scores["spo2"] = 25
                recommendations.append("⚠️ Critically low oxygen. Seek immediate care.")

        # Temperature Score
        if vitals and vitals.temperature_c:
            temp = float(vitals.temperature_c)
            if 36.1 <= temp <= 37.2:
                scores["temp"] = 100
            elif 35.5 <= temp <= 37.8:
                scores["temp"] = 75
            elif 35.0 <= temp <= 38.5:
                scores["temp"] = 50
                recommendations.append("Temperature slightly abnormal.")
            else:
                scores["temp"] = 25
                recommendations.append("Significant temperature abnormality.")

        # BMI Score
        if bmi:
            if 18.5 <= bmi <= 24.9:
                scores["bmi"] = 100
            elif 25 <= bmi <= 29.9:
                scores["bmi"] = 70
                recommendations.append("BMI indicates overweight. Consider lifestyle changes.")
            elif 30 <= bmi <= 34.9:
                scores["bmi"] = 45
                recommendations.append("BMI indicates obesity. Discuss with your doctor.")
            elif bmi < 18.5:
                scores["bmi"] = 55
                recommendations.append("BMI indicates underweight.")
            else:
                scores["bmi"] = 30
                recommendations.append("BMI indicates severe obesity.")

        # Medication Adherence Score
        if adherence is not None:
            scores["adherence"] = min(100, adherence)
            if adherence < 50:
                recommendations.append("Medication adherence is very low. This affects your health.")
            elif adherence < 80:
                recommendations.append("Try to improve medication adherence.")

        # AI Risk Score (inverted — lower risk = higher score)
        if latest_risk_scores:
            avg_risk = sum(latest_risk_scores) / len(latest_risk_scores)
            scores["risk"] = max(0, 100 - (avg_risk * 100))
            if avg_risk > 0.7:
                recommendations.append("AI risk assessment is high. Review with your doctor.")
            elif avg_risk > 0.4:
                recommendations.append("Moderate AI risk detected. Stay proactive.")

        # Calculate weighted composite
        if not scores:
            return {
                "score": 0,
                "grade": "N/A",
                "color": "#999",
                "breakdown": {},
                "recommendations": ["No vitals data available. Submit a reading to get your health score."],
            }

        total_weight = 0
        weighted_sum = 0
        for key, weight in self.WEIGHTS.items():
            if key in scores:
                weighted_sum += float(scores[key]) * weight
                total_weight += weight

        composite = round(weighted_sum / total_weight) if total_weight > 0 else 0

        # Grade
        if composite >= 90:
            grade, color = "Excellent", "#0E7A5C"
        elif composite >= 75:
            grade, color = "Good", "#0E7A5C"
        elif composite >= 60:
            grade, color = "Fair", "#B8761D"
        elif composite >= 40:
            grade, color = "Needs Attention", "#B8761D"
        else:
            grade, color = "Critical", "#C73E3A"

        if not recommendations:
            recommendations.append("Your health indicators look good. Keep it up!")

        return {
            "score": composite,
            "grade": grade,
            "color": color,
            "breakdown": scores,
            "recommendations": recommendations[:5],
        }
