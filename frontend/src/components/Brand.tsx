import { AudioLines } from "lucide-react";

export default function Brand() {
  return (
    <a className="brand" href="#" aria-label="Briefly home">
      <span className="brand-mark"><AudioLines size={19} strokeWidth={2.4} /></span>
      <span>briefly<span className="brand-period">.</span></span>
    </a>
  );
}
