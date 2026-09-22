#include "MySensitiveDetector.hh"

MySensitiveDetector::MySensitiveDetector(G4String name)
    : G4VSensitiveDetector(name) {
    fTotalEnergyDeposited = 0.;
}

MySensitiveDetector::~MySensitiveDetector() {}

void MySensitiveDetector::Initialize(G4HCofThisEvent*) {
    fTotalEnergyDeposited = 0.;
}

void MySensitiveDetector::EndOfEvent(G4HCofThisEvent*) {
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillH1(0, fTotalEnergyDeposited);

    // G4cout << "Deposited energy: " << fTotalEnergyDeposited << G4endl;
}

G4bool MySensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*) {
    G4int eventID =
        G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();

    G4StepPoint* preStepPoint = step->GetPreStepPoint();
    // Check if the particle is entering the volume for the first time
    if (preStepPoint->GetStepStatus() == fGeomBoundary) {
        G4String nameDet = preStepPoint->GetSensitiveDetector()->GetName();
        // G4String nameDet = step->GetTrack()->GetVolume()->GetName();
        G4double energyDeposited = step->GetTotalEnergyDeposit();

        G4Track* track = step->GetTrack();
        G4double kinEnergy = track->GetKineticEnergy();
        G4int trackID = track->GetTrackID();
        G4String particleName = track->GetDefinition()->GetParticleName();

        G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
        analysisManager->FillNtupleIColumn(0, 0, eventID);
        analysisManager->FillNtupleSColumn(0, 1, nameDet);
        analysisManager->FillNtupleDColumn(0, 2, energyDeposited);
        analysisManager->FillNtupleDColumn(0, 3, kinEnergy);
        analysisManager->FillNtupleIColumn(0, 4, trackID);
        analysisManager->FillNtupleSColumn(0, 5, particleName);
        analysisManager->AddNtupleRow(0);  // the row is complete

        if (energyDeposited > 0) {
            fTotalEnergyDeposited += energyDeposited;
        }
    }

    return true;
}