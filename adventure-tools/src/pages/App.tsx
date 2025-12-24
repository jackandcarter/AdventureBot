import { useMemo, useState } from "react";
import { Layout } from "../components/Layout";
import { AbilitiesPage } from "./AbilitiesPage";
import { ClassesPage } from "./ClassesPage";
import { EnemiesPage } from "./EnemiesPage";
import { ItemsPage } from "./ItemsPage";

export function App() {
  const [active, setActive] = useState("Enemies");
  const content = useMemo(() => {
    switch (active) {
      case "Items":
        return <ItemsPage />;
      case "Classes":
        return <ClassesPage />;
      case "Abilities":
        return <AbilitiesPage />;
      case "Enemies":
      default:
        return <EnemiesPage />;
    }
  }, [active]);

  return (
    <Layout active={active} onNavChange={setActive}>
      {content}
    </Layout>
  );
}
