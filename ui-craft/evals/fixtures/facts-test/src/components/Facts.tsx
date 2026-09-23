import { Home, Bogus, Settings } from "lucide-react";
import { AcademicCapIcon, FakeIcon } from "@heroicons/react/24/outline";
import { useState } from "react";
import { fancy } from "not-installed-pkg";

export function Facts() {
  const [n] = useState(0);
  return (
    <div>
      <Home /> <Bogus /> <Settings /> <AcademicCapIcon /> <FakeIcon />
      <button>{fancy(n)}</button>
    </div>
  );
}
