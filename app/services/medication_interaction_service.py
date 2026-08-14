"""
medication_interaction_service.py
----------------------------------
Checks for potential medication interactions and contraindications
based on a predefined knowledge base of common drug interactions.
"""


class MedicationInteractionService:

    # Common drug interaction pairs: (drug_a, drug_b, severity, description)
    KNOWN_INTERACTIONS = [
        ("warfarin", "aspirin", "high",
         "Increased bleeding risk. Monitor closely and consider alternatives."),
        ("warfarin", "ibuprofen", "high",
         "NSAIDs increase bleeding risk with warfarin."),
        ("warfarin", "naproxen", "high",
         "NSAIDs increase bleeding risk with warfarin."),
        ("metformin", "alcohol", "high",
         "Alcohol increases risk of lactic acidosis with metformin."),
        ("metformin", "contrast dye", "high",
         "Hold metformin before/after IV contrast to prevent kidney damage."),
        ("lisinopril", "potassium", "medium",
         "ACE inhibitors can increase potassium levels. Monitor potassium."),
        ("lisinopril", "spironolactone", "medium",
         "Combined use can cause hyperkalemia."),
        ("aspirin", "ibuprofen", "medium",
         "NSAIDs may reduce the cardioprotective effect of aspirin."),
        ("aspirin", "naproxen", "medium",
         "NSAIDs may reduce the cardioprotective effect of aspirin."),
        ("atorvastatin", "grapefruit", "low",
         "Grapefruit can increase statin levels. Limit intake."),
        ("atorvastatin", "erythromycin", "medium",
         "Macrolide antibiotics can increase statin levels."),
        ("atorvastatin", "clarithromycin", "medium",
         "Macrolide antibiotics can increase statin levels."),
        ("glipizide", "fluconazole", "medium",
         "Azole antifungals can enhance sulfonylurea effect."),
        ("metformin", "glipizide", "low",
         "Combination is common but monitor for hypoglycemia."),
        ("amlodipine", "simvastatin", "medium",
         "Limit simvastatin dose to 20mg with amlodipine."),
        ("clopidogrel", "omeprazole", "medium",
         "PPIs may reduce effectiveness of clopidogrel."),
        ("methotrexate", "ibuprofen", "high",
         "NSAIDs can increase methotrexate toxicity."),
        ("lithium", "ibuprofen", "high",
         "NSAIDs can increase lithium levels to toxic range."),
        ("digoxin", "amiodarone", "high",
         "Amiodarone increases digoxin levels. Reduce digoxin dose."),
    ]

    def check_interactions(self, medication_names: list[str]) -> list[dict]:
        """
        Check a list of medication names for known interactions.
        Returns list of interaction dicts with severity and description.
        """
        interactions = []
        checked = set()

        for i, med_a in enumerate(medication_names):
            for med_b in medication_names[i + 1:]:
                pair = tuple(sorted([med_a.lower(), med_b.lower()]))
                if pair in checked:
                    continue
                checked.add(pair)

                for known_a, known_b, severity, desc in self.KNOWN_INTERACTIONS:
                    if (known_a in med_a.lower() and known_b in med_b.lower()) or \
                       (known_b in med_a.lower() and known_a in med_b.lower()):
                        interactions.append({
                            "drug_a": med_a,
                            "drug_b": med_b,
                            "severity": severity,
                            "description": desc,
                            "icon": {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(severity, "⚪"),
                        })

        return interactions

    def get_medication_warnings(self, medication_names: list[str]) -> list[str]:
        """Return simple warning strings for display."""
        interactions = self.check_interactions(medication_names)
        return [
            f"{i['icon']} **{i['drug_a']}** + **{i['drug_b']}** ({i['severity'].upper()}): {i['description']}"
            for i in interactions
        ]
