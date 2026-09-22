#include "MyTrackingAction.hh"

#include "G4AnalysisManager.hh"
#include "G4Event.hh"
#include "G4ParticleDefinition.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

MyTrackingAction::MyTrackingAction() = default;
MyTrackingAction::~MyTrackingAction() = default;

void MyTrackingAction::SetMotherInfo(const G4Track* secondaryTrack,
                                     const G4String& motherName,
                                     G4int motherPDG, G4double motherEkin,
                                     G4double motherMass,
                                     G4double motherMomentum,
                                     G4double motherEtot, G4int nDaugh) {
    fMotherInfoMap[secondaryTrack] =
        MotherInfo{motherName,     motherPDG,  motherEkin, motherMass,
                   motherMomentum, motherEtot, nDaugh};
}

void MyTrackingAction::SetReactionInfo(
    const G4Track* secondaryTrack, const G4String& motherName, G4int motherPDG,
    G4double motherEkin, G4double motherMass, G4double motherMomentum,
    G4double motherEtot, G4int nDaugh, const TargetNucleusInfo& targetInfo) {
    fReactionInfoMap[secondaryTrack] =
        ReactionInfo{motherName,     motherPDG,  motherEkin, motherMass,
                     motherMomentum, motherEtot, nDaugh,     targetInfo};
}

void MyTrackingAction::PreUserTrackingAction(const G4Track* track) {
    G4int eventID =
        G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
    G4int trackID = track->GetTrackID();
    G4int parentID = track->GetParentID();  // 0 = particule primaire
    G4double momentum = track->GetMomentum().mag();

    const G4ParticleDefinition* def = track->GetDefinition();
    G4String particleName = def->GetParticleName();
    G4int pdgCode = def->GetPDGEncoding();
    G4double mass = def->GetPDGMass();

    G4String creatorProcess = "Primary";
    bool isSecondary = false;
    if (parentID != 0) {
        const G4VProcess* proc = track->GetCreatorProcess();
        creatorProcess = proc ? proc->GetProcessName() : "unknown";
        isSecondary = true;
    }

    // if (!isSecondary) return;

    if (creatorProcess != "ionInelastic")
        return;  // only keep ionInelastic processes

    const G4ThreeVector& vertexPos = track->GetVertexPosition();
    G4double kinE = track->GetVertexKineticEnergy();

    // G4double totE = track->GetStep()->GetPreStepPoint()->GetTotalEnergy();

    // GetGlobalTime() au moment de PreUserTrackingAction == temps de
    // creation de la piste (aucun step n'a encore ete effectue). Sert
    // d'indicateur temporel pour distinguer des vertex a la meme position
    // spatiale mais crees a des instants differents.
    G4double vertexTime = track->GetGlobalTime();

    // Identite/energie de la mere, transmises par SteppingAction au moment
    // ou elle a cree CETTE piste. Absentes pour la particule primaire
    // (parentID == 0) -> valeurs par defaut ci-dessous.
    G4String motherName = "none";
    G4int motherPDG = 0;
    G4double motherEkin = -1.;  // -1 MeV = non applicable
    G4double motherMass = -1.;
    G4double motherMomentum = -1.;
    G4double motherEtot = -1.;
    G4int nDaugh = -1;

    TargetNucleusInfo target;  // valeurs par defaut (isValid = false)

    auto it = fReactionInfoMap.find(track);
    if (it != fReactionInfoMap.end()) {
        motherName = it->second.motherName;
        motherPDG = it->second.motherPDG;
        motherEkin = it->second.motherEkin;
        motherMass = it->second.motherMass;
        motherMomentum = it->second.motherMomentum;
        motherEtot = it->second.motherEtot;
        nDaugh = it->second.nDaugh;
        target = it->second.target;
        fReactionInfoMap.erase(
            it);  // entree consommee, plus necessaire ensuite
    }

    // auto it = fMotherInfoMap.find(track);
    // if (it != fMotherInfoMap.end()) {
    //     motherName = it->second.name;
    //     motherPDG = it->second.pdg;
    //     motherEkin = it->second.ekin;
    //     motherMass = it->second.mass;
    //     motherMomentum = it->second.momentum;
    //     motherEtot = it->second.etot;
    //     nDaugh = it->second.nDaugh;
    //     fMotherInfoMap.erase(it);  // entree consommee, plus necessaire
    //     ensuite
    // }

    auto analysisManager = G4AnalysisManager::Instance();
    const G4int idNtupleMcTruth = 0;
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 0, eventID);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 1, trackID);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 2, parentID);
    analysisManager->FillNtupleSColumn(idNtupleMcTruth, 3, particleName);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 4, pdgCode);
    analysisManager->FillNtupleSColumn(idNtupleMcTruth, 5, creatorProcess);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 6, vertexPos.x() / cm);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 7, vertexPos.y() / cm);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 8, vertexPos.z() / cm);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 9, vertexTime / ns);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 10, kinE / MeV);
    analysisManager->FillNtupleSColumn(idNtupleMcTruth, 11, motherName);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 12, motherPDG);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 13, motherEkin / MeV);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 14, motherMass / MeV);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 15,
                                       motherMomentum / MeV);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 16, momentum / MeV);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 17, mass / MeV);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 18, motherEtot / MeV);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 19, nDaugh);
    // --- Noyau cible de la reaction (uniquement rempli pour les
    // reactions hadroniques -- voir SteppingAction) ---
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 20, target.Z);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 21, target.A);
    analysisManager->FillNtupleSColumn(idNtupleMcTruth, 22, target.name);
    analysisManager->FillNtupleIColumn(idNtupleMcTruth, 23, target.pdg);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 24, target.mass_MeV);
    analysisManager->FillNtupleDColumn(idNtupleMcTruth, 25, target.ekin_MeV);
    if (target.isValid) {
        analysisManager->FillNtupleDColumn(idNtupleMcTruth, 26,
                                           target.position.x() / cm);
        analysisManager->FillNtupleDColumn(idNtupleMcTruth, 27,
                                           target.position.y() / cm);
        analysisManager->FillNtupleDColumn(idNtupleMcTruth, 28,
                                           target.position.z() / cm);
    } else {
        analysisManager->FillNtupleDColumn(idNtupleMcTruth, 29, -9999.);
        analysisManager->FillNtupleDColumn(idNtupleMcTruth, 30, -9999.);
        analysisManager->FillNtupleDColumn(idNtupleMcTruth, 31, -9999.);
    }
    analysisManager->AddNtupleRow(idNtupleMcTruth);
}
