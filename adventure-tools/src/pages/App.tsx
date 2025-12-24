import { useMemo, useState } from "react";
import { Layout } from "../components/Layout";
import { AbilitiesPage } from "./AbilitiesPage";
import { ClassesPage } from "./ClassesPage";
import { EidolonsPage } from "./EidolonsPage";
import { EnemiesPage } from "./EnemiesPage";
import { ItemsPage } from "./ItemsPage";
import { OverviewPage } from "./OverviewPage";
import { ResistancesPage } from "./ResistancesPage";
import { RoomTemplatesPage } from "./RoomTemplatesPage";
import { TranceAbilitiesPage } from "./TranceAbilitiesPage";
import { VendorsPage } from "./VendorsPage";

export function App() {
  const [active, setActive] = useState("Enemies");
  const content = useMemo(() => {
    switch (active) {
      case "Overview":
        return <OverviewPage />;
      case "Items":
        return <ItemsPage />;
      case "Classes":
        return <ClassesPage />;
      case "Abilities":
        return <AbilitiesPage />;
      case "Resistances":
        return <ResistancesPage />;
      case "Room Templates":
        return <RoomTemplatesPage />;
      case "Eidolons":
        return <EidolonsPage />;
      case "Trance Abilities":
        return <TranceAbilitiesPage />;
      case "Vendors":
        return <VendorsPage />;
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
