#include "MyRunAction.hh"

MyRunAction::MyRunAction() {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->CreateH1("Edep", "Energy deposit", 100, 0., 1.1 * MeV);

    const G4int idNtuple = 0;
    analysisManager->CreateNtuple("tree", "tree");
    analysisManager->CreateNtupleIColumn(idNtuple, "iEvent");
    analysisManager->CreateNtupleSColumn(idNtuple, "nameDet");
    analysisManager->CreateNtupleDColumn(idNtuple, "Edep_MeV");
    analysisManager->CreateNtupleDColumn(idNtuple, "Ekin_MeV");
    analysisManager->CreateNtupleIColumn(idNtuple, "trackID");
    analysisManager->CreateNtupleSColumn(idNtuple, "ParticleName");
    analysisManager->FinishNtuple(idNtuple);

    // fRootTree->Branch("EventNb"  , &fEvent,"EventNb   /I") ;
    //   fRootTree->Branch("ptclName" , &fParticleName) ;
    //   fRootTree->Branch("detName" , &fDetectorName) ;
    //   fRootTree->Branch("parentID" , &fParentID  ,"parentID  /I") ;
    //   fRootTree->Branch("trackID"  , &fTrackID  ,"trackID  /I") ;
    //   fRootTree->Branch("Einit_MeV", &fEinit,"Einit_MeV /D") ;
    //   fRootTree->Branch("Ekin_MeV" , &fEkin ,"Ekin_MeV  /D") ;
    //   fRootTree->Branch("X_mm"    , &fX    ,"X_mm     /D") ;
    //   fRootTree->Branch("Y_mm"    , &fY    ,"Y_mm     /D") ;
    //   fRootTree->Branch("Z_mm"    , &fZ    ,"Z_mm     /D") ;
    //   fRootTree->Branch("VtxX_mm", &fVtxX,"VtxX_mm     /D") ;
    //   fRootTree->Branch("VtxY_mm", &fVtxY,"VtxY_mm     /D") ;
    //   fRootTree->Branch("VtxZ_mm", &fVtxZ,"VtxZ_mm     /D") ;
    //   fRootTree->Branch("theta"    , &fTheta,"theta /D") ;
    //   fRootTree->Branch("Edep_MeV" , &fEdep ,"Edep_MeV  /D") ;
    //   fRootTree->Branch("range"    , &fRange,"range /D") ;
    //   fRootTree->Branch("track"    , &fTrackL,"track /D") ;

    // analysisManager->CreateNtuple("Photons", "Photons");
    // analysisManager->CreateNtupleIColumn("iEvent");
    // analysisManager->CreateNtupleDColumn("fX");
    // analysisManager->CreateNtupleDColumn("fY");
    // analysisManager->CreateNtupleDColumn("fZ");
    // analysisManager->CreateNtupleDColumn("fGlobalTime");
    // analysisManager->CreateNtupleDColumn("fWlen");
    // analysisManager->FinishNtuple(0);
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