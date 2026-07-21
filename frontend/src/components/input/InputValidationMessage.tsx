export default function InputValidationMessage({ message }: { message?: string }) {
  return message ? <p className="error-message" role="alert">{message}</p> : null;
}
