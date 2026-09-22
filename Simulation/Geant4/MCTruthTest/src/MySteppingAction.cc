#include "MySteppingAction.hh"

#include "G4HadronicProcess.hh"
#include "G4IonTable.hh"
#include "G4NucleiProperties.hh"
#include "G4Nucleus.hh"
#include "G4ParticleDefinition.hh"
#include "G4Step.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"
#include "MyTrackingAction.hh"

MySteppingAction::MySteppingAction(MyTrackingAction* trackingAction)
    : fTrackingAction(trackingAction) {}

MySteppingAction::~MySteppingAction() = default;

void MySteppingAction::UserSteppingAction(const G4Step* step) {
    // Secondaires produits PENDANT ce step (peut etre nullptr ou vide la
    // plupart du temps -- la majorite des steps ne produisent rien).
    const std::vector<const G4Track*>* secondaries =
        step->GetSecondaryInCurrentStep();
    if (!secondaries || secondaries->empty()) return;

    const G4Track* motherTrack = step->GetTrack();
    const G4ParticleDefinition* motherDef = motherTrack->GetDefinition();

    auto motherParentID = motherTrack->GetParentID();

    if (motherParentID != 0) return;  // FIXME test

    G4String motherName = motherDef->GetParticleName();
    G4int motherPDG = motherDef->GetPDGEncoding();
    G4double motherMass = motherDef->GetPDGMass();

    // Energie cinetique de la mere APRES ce step, c-a-d juste apres avoir
    // cree ces secondaires (avant qu'elle ne perde davantage d'energie aux
    // steps suivants, ou soit elle-meme detruite par la reaction).
    G4double motherEkin =
        step->GetPreStepPoint()->GetKineticEnergy();  // get Ekin before decay
    // motherTrack->GetKineticEnergy();
    G4double motherMomentum = step->GetPreStepPoint()->GetMomentum().mag();
    G4double motherEtot = step->GetPreStepPoint()->GetTotalEnergy();

    G4int nDaugh = secondaries->size();

    // --- Noyau cible de la reaction ---
    // Le process qui a agi en fin de step (celui qui a genere les
    // secondaires) est recupere via GetProcessDefinedStep(). S'il s'agit
    // d'un G4HadronicProcess (reaction nucleaire : inelastique, elastique,
    // capture, fission...), on recupere le noyau cible via
    // GetTargetNucleus(). Pour un process non-hadronique (ex. ionIoni qui
    // produit un rayon delta electronique), il n'y a pas de "noyau cible"
    // au sens nucleaire -> TargetNucleusInfo reste a ses valeurs par defaut.
    TargetNucleusInfo targetInfo;  // isValid = false par defaut

    G4VProcess* proc = const_cast<G4VProcess*>(
        step->GetPostStepPoint()->GetProcessDefinedStep());
    auto hadProcess = dynamic_cast<G4HadronicProcess*>(proc);

    if (hadProcess) {
        // NOTE : selon la version de Geant4 installee, GetTargetNucleus()
        // peut renvoyer un G4Nucleus* ou une reference const G4Nucleus&. Si
        // la ligne suivante ne compile pas telle quelle, remplace
        // "G4Nucleus* nucleus = hadProcess->GetTargetNucleus();"
        // par
        // "G4Nucleus* nucleus = &hadProcess->GetTargetNucleus();" (ou
        // l'inverse).
        const G4Nucleus* nucleus = hadProcess->GetTargetNucleus();

        if (nucleus) {
            G4int Z = nucleus->GetZ_asInt();
            G4int A = nucleus->GetA_asInt();

            // if (Z != 1 and Z != 8)
            //     return;  // FIXME to test if I still get C12 as target

            if (Z > 0 && A > 0) {
                targetInfo.isValid = true;
                targetInfo.Z = Z;
                targetInfo.A = A;
                targetInfo.mass_MeV =
                    G4NucleiProperties::GetNuclearMass(A, Z) / MeV;
                // Convention : noyau cible au repos dans le referentiel labo
                // (approximation standard des modeles hadroniques utilises ici,
                // le mouvement de Fermi eventuel n'est pas expose ici).
                targetInfo.ekin_MeV = 0.;
                targetInfo.position = step->GetPostStepPoint()->GetPosition();

                // Nom/PDG via la table des ions (ex. "O16")
                G4ParticleDefinition* ionDef =
                    G4IonTable::GetIonTable()->GetIon(Z, A, 0.);
                if (ionDef) {
                    targetInfo.name = ionDef->GetParticleName();
                    targetInfo.pdg = ionDef->GetPDGEncoding();
                }
            }
        }
    }

    for (const G4Track* secondary : *secondaries) {
        // fTrackingAction->SetMotherInfo(secondary, motherName, motherPDG,
        //                                motherEkin, motherMass,
        //                                motherMomentum, motherEtot, nDaugh,
        //                                targetInfo);
        fTrackingAction->SetReactionInfo(secondary, motherName, motherPDG,
                                         motherEkin, motherMass, motherMomentum,
                                         motherEtot, nDaugh, targetInfo);
    }
}
