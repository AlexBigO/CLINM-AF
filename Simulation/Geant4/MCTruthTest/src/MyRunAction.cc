#include "MyRunAction.hh"

MyRunAction::MyRunAction() {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->SetVerboseLevel(0);
    analysisManager->SetDefaultFileType("root");

    const G4int idNtupleMcTruth = 0;

    analysisManager->CreateNtuple("Tracks", "Historique des particules");
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth,
                                         "EventID");  // colonne 0
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth,
                                         "TrackID");  // colonne 1
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth,
                                         "ParentID");  // colonne 2
    analysisManager->CreateNtupleSColumn(idNtupleMcTruth,
                                         "Particle");  // colonne 3
    analysisManager->CreateNtupleIColumn(
        idNtupleMcTruth,
        "PDGCode");  // colonne 4  (bonus : PDG de la particule courante)
    analysisManager->CreateNtupleSColumn(idNtupleMcTruth,
                                         "CreatorProcess");  // colonne 5
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth,
                                         "VertexX_cm");  // colonne 6
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth,
                                         "VertexY_cm");  // colonne 7
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth,
                                         "VertexZ_cm");  // colonne 8
    analysisManager->CreateNtupleDColumn(
        "Time_ns");  // colonne 9  (NOUVEAU : temps de creation)
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth,
                                         "Ekin_MeV");  // colonne 10
    analysisManager->CreateNtupleSColumn(idNtupleMcTruth,
                                         "MotherName");  // colonne 11 (NOUVEAU)
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth,
                                         "MotherPDG");  // colonne 12 (NOUVEAU)
    analysisManager->CreateNtupleDColumn(
        idNtupleMcTruth,
        "MotherEkin_MeV");  // colonne 13 (NOUVEAU)
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "MotherMass_MeV");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "MotherMomentum_MeV");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "Momentum_MeV");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "Mass_MeV");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "MotherEtot_MeV");
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth, "Ndaughters");
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth, "TargetZ");
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth, "TargetA");
    analysisManager->CreateNtupleSColumn(idNtupleMcTruth, "TargetName");
    analysisManager->CreateNtupleIColumn(idNtupleMcTruth, "TargetPDG");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "TargetMass_MeV");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "TargetEkin_MeV");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "TargetX_cm");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "TargetY_cm");
    analysisManager->CreateNtupleDColumn(idNtupleMcTruth, "TargetZ_cm");
    analysisManager->FinishNtuple(idNtupleMcTruth);

    // analysisManager->CreateH1("Edep", "Energy deposit", 100, 0., 1.1 * MeV);

    // const G4int idNtuple = 0;
    // analysisManager->CreateNtuple("tree", "tree");
    // analysisManager->CreateNtupleIColumn(idNtuple, "iEvent");
    // analysisManager->CreateNtupleSColumn(idNtuple, "nameDet");
    // analysisManager->CreateNtupleDColumn(idNtuple, "Edep_MeV");
    // analysisManager->CreateNtupleDColumn(idNtuple, "Ekin_MeV");
    // analysisManager->CreateNtupleIColumn(idNtuple, "trackID");
    // analysisManager->CreateNtupleSColumn(idNtuple, "ParticleName");
    // analysisManager->FinishNtuple(idNtuple);
}

MyRunAction::~MyRunAction() {}

void MyRunAction::BeginOfRunAction(const G4Run* run) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    G4int runID = run->GetRunID();
    std::stringstream strRunID;
    strRunID << runID;
    analysisManager->OpenFile("output" + strRunID.str() + ".root");
    // analysisManager->OpenFile("output.root");
}

void MyRunAction::EndOfRunAction(const G4Run* run) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();

    analysisManager->Write();  // write the file at the end of each run
    analysisManager->CloseFile();

    G4int runID = run->GetRunID();
    G4cout << "Finishing run " << runID << G4endl;
}