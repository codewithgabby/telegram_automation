
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import App from "./App";
import ContinuePage from "./ContinuePage";

const currentPath = window.location.pathname.replace(/\/+$/, "");

const isContinuationPage = currentPath === "/continue";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {isContinuationPage ? <ContinuePage /> : <App />}
  </StrictMode>
);
