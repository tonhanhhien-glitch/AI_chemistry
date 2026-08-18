import { createBrowserRouter } from "react-router-dom";

import AnalysisPage from "./pages/AnalysisPage";
import ExamplesPage from "./pages/ExamplesPage";
import HomePage from "./pages/HomePage";
import MoleculeDataPage from "./pages/MoleculeDataPage";
import NotFoundPage from "./pages/NotFoundPage";
import RulesPage from "./pages/RulesPage";
import SurveyPage from "./pages/SurveyPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/analysis",
    element: <AnalysisPage />,
  },
  {
    path: "/examples",
    element: <ExamplesPage />,
  },
  {
    path: "/rules",
    element: <RulesPage />,
  },
  {
    path: "/survey",
    element: <SurveyPage />,
  },
  {
    // Not linked from the main nav -- reachable only by direct URL, consistent
    // with this being a private admin interface rather than a student-facing page.
    path: "/admin",
    element: <MoleculeDataPage />,
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
