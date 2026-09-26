// frontend/src/components/risk/InteractionChecker.jsx

import { useState } from "react";
import { checkInteractions } from "../../api/risk";
import SeverityBadge from "./SeverityBadge";

function parseList(text) {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function InteractionChecker() {
  const [medications, setMedications] = useState("Warfarin, Ibuprofen");
  const [allergies, setAllergies] = useState("");
  const [foodItems, setFoodItems] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await checkInteractions({
        medications: parseList(medications),
        allergies: parseList(allergies),
        foodItems: parseList(foodItems),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const hasWarnings =
    result &&
    (result.drug_interactions.length > 0 ||
      result.allergy_warnings.length > 0 ||
      result.food_warnings.length > 0);

  return (
    <div>
      <form onSubmit={handleSubmit} className="risk-form">
        <label className="risk-label">
          Medications
          <input
            className="risk-input"
            value={medications}
            onChange={(e) => setMedications(e.target.value)}
            placeholder="Warfarin, Ibuprofen"
          />
        </label>

        <label className="risk-label">
          Allergies <span className="risk-optional">(optional)</span>
          <input
            className="risk-input"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            placeholder="Penicillin"
          />
        </label>

        <label className="risk-label">
          Food / lifestyle items <span className="risk-optional">(optional)</span>
          <input
            className="risk-input"
            value={foodItems}
            onChange={(e) => setFoodItems(e.target.value)}
            placeholder="Grapefruit, Alcohol"
          />
        </label>

        <button className="risk-button" type="submit" disabled={loading}>
          {loading ? "Checking..." : "Check interactions"}
        </button>
      </form>

      {error && <div className="risk-error">{error}</div>}

      {result && (
        <div className="risk-result">
          <p className="risk-summary">{result.summary}</p>

          {!hasWarnings && (
            <p className="risk-empty">No conflicts found in this combination.</p>
          )}

          {result.drug_interactions.map((item, i) => (
            <div key={`drug-${i}`} className="risk-card">
              <div className="risk-card-head">
                <span className="risk-card-title">
                  {item.drug_a} + {item.drug_b}
                </span>
                <SeverityBadge severity={item.severity} />
              </div>
              <p className="risk-hazard">{item.hazard}</p>
              <p className="risk-explanation">{item.explanation}</p>
            </div>
          ))}

          {result.allergy_warnings.map((item, i) => (
            <div key={`allergy-${i}`} className="risk-card">
              <div className="risk-card-head">
                <span className="risk-card-title">
                  {item.medication} — {item.allergen} allergy
                </span>
                <SeverityBadge severity={item.severity} />
              </div>
              <p className="risk-explanation">{item.explanation}</p>
            </div>
          ))}

          {result.food_warnings.map((item, i) => (
            <div key={`food-${i}`} className="risk-card">
              <div className="risk-card-head">
                <span className="risk-card-title">
                  {item.medication} + {item.food_item}
                </span>
                <SeverityBadge severity={item.severity} />
              </div>
              <p className="risk-explanation">{item.explanation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
