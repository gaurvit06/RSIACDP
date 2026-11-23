import { ChartColumn } from 'lucide-react';
import { Assessment } from './Assessment';
export type Prediction = {
  label: string; score: number | null; model_version: string; threshold: number; matched_words: number;
};

export function predictionLabel(prediction: Prediction | null | undefined, status: string) {
  if (prediction) return prediction.label;
  return ['queued', 'processing'].includes(status) ? 'Awaiting processing' : 'Unscored';
}

export function PostingPrediction({ prediction, status, evidence }: {
  prediction?: Prediction | null; status: string; evidence: string;
}) {
  return <section className="reading-card reading-model">
    <h2><ChartColumn size={19} aria-hidden="true"/>What the model predicts</h2>
    <Assessment>{predictionLabel(prediction, status)}</Assessment>
    <p>{prediction?.score === null
      ? 'Submit more of the posting. The model needs at least three distinct words it recognizes.'
      : 'The model estimates fraud risk from the wording and details of the posting.'}</p>
    {prediction?.label === 'Lower fraud risk' && evidence === 'Evidence supports concern' &&
      <p className="modal-warning"><strong>Check the evidence.</strong> A source finding raises a concern despite the lower model score.</p>}
    {prediction && <details className="model-method"><summary>How the model decided</summary>
      <p>The hiring-market logistic regression model uses company details, requirements, salary disclosure, logo presence, description length and urgency wording. Missing fields use the dashboard defaults.</p>
      {prediction.score !== null && <p><b>Score {prediction.score.toFixed(3)}</b> · Higher risk starts at {prediction.threshold.toFixed(2)}.</p>}
      <small>{prediction.matched_words} recognized words · {prediction.model_version}</small>
    </details>}
  </section>;
}
