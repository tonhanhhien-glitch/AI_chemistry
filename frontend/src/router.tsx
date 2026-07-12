import { createBrowserRouter } from "react-router-dom";

import AnalysisPage from "./pages/AnalysisPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";

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
    path: "*",
    element: <NotFoundPage />,
  },
]);
