import { useMemo, useState } from "react";
import { Layout } from "../components/Layout";
import { EnemiesPage } from "./EnemiesPage";
import { ItemsPage } from "./ItemsPage";

const navItems = [
  "Overview",
  "Enemies",
  "Items",
  "Classes",
  "Abilities",
  "Resistances",
  "Room Templates",
  "Eidolons",
  "Trance Abilities",
  "Vendors"
];

export function App() {
  const [activeTab, setActiveTab] = useState("Enemies");
  const content = useMemo(() => {
    switch (activeTab) {
      case "Items":
        return <ItemsPage />;
      case "Enemies":
      default:
        return <EnemiesPage />;
    }
  }, [activeTab]);

  return (
    <Layout items={navItems} active={activeTab} onSelect={setActiveTab}>
      {content}
    </Layout>
  );
}
