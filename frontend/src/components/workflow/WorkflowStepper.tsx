import { useI18n } from "../../i18n";

const stepKeys = ["workflow.step.input", "workflow.step.lewis", "workflow.step.axen", "workflow.step.geometry", "workflow.step.model3d", "workflow.step.explanation"];

export default function WorkflowStepper({ active = 6 }: { active?: number }) {
  const { t } = useI18n();
  return <ol className="stepper" aria-label={t("workflow.stepper.aria")}>{stepKeys.map((stepKey, index) => <li key={stepKey} className={index < active ? "complete" : ""}><span>{index + 1}</span>{t(stepKey)}</li>)}</ol>;
}
