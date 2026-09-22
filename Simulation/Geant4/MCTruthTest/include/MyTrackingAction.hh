#ifndef MYTRACKINGACTION_H
#define MYTRACKINGACTION_H  // 1

#include <map>

#include "G4ThreeVector.hh"
#include "G4UserTrackingAction.hh"
#include "globals.hh"

class G4Track;

// Informations sur le noyau cible d'une reaction hadronique (rempli par
// SteppingAction seulement si le step correspond a un G4HadronicProcess ;
// sinon isValid reste false et les champs gardent leurs valeurs par defaut).
struct TargetNucleusInfo {
    G4bool isValid = false;
    G4int Z = 0;
    G4int A = 0;
    G4String name = "none";
    G4int pdg = 0;
    G4double mass_MeV = -1.;
    G4double ekin_MeV =
        -1.;  // convention : noyau cible au repos -> 0 si isValid
    G4double momentum_MeV = -1.;
    G4double etot_MeV = -1.;
    G4int nDaugh = -1;
    G4ThreeVector
        position;  // position de l'interaction (mm, unites internes Geant4)
};

// Appelee automatiquement par Geant4 pour CHAQUE piste (primaire ou
// secondaire), juste avant qu'elle ne soit propagee. C'est ici qu'on a
// acces au process createur, au parent, et a la position/energie/temps
// de creation -- independamment de toute geometrie de detecteur.
class MyTrackingAction : public G4UserTrackingAction {
   public:
    MyTrackingAction();
    ~MyTrackingAction() override;

    void PreUserTrackingAction(const G4Track* track) override;

    // Appele par SteppingAction : enregistre l'identite et l'energie
    // cinetique de la mere pour la piste fille "secondaryTrack", au moment
    // ou celle-ci vient d'etre creee.
    //
    // IMPORTANT : on indexe par pointeur G4Track* (stable et identique aux
    // deux endroits), PAS par TrackID. En effet, au moment ou SteppingAction
    // s'execute, le TrackID final de la piste fille n'est pas encore fixe
    // (il n'est assigne qu'apres que la piste mere ait entierement fini
    // d'etre trackee) -- indexer par TrackID ferait systematiquement
    // echouer la recherche plus tard dans PreUserTrackingAction.
    void SetMotherInfo(const G4Track* secondaryTrack,
                       const G4String& motherName, G4int motherPDG,
                       G4double motherEkin, G4double motherMass,
                       G4double motherMomentum, G4double motherEtot,
                       G4int nDaugh);

    void SetReactionInfo(const G4Track* secondaryTrack,
                         const G4String& motherName, G4int motherPDG,
                         G4double motherEkin, G4double motherMass,
                         G4double motherMomentum, G4double motherEtot,
                         G4int nDaugh, const TargetNucleusInfo& targetInfo);

   private:
    struct MotherInfo {
        G4String name;
        G4int pdg;
        G4double ekin;
        G4double mass;
        G4double momentum;
        G4double etot;
        G4int nDaugh;
    };

    struct ReactionInfo {
        G4String motherName;
        G4int motherPDG;
        G4double motherEkin;
        G4double motherMass;
        G4double motherMomentum;
        G4double motherEtot;
        G4int nDaugh;
        TargetNucleusInfo target;
    };

    // Cle = pointeur vers la piste fille. Rempli par SteppingAction, consomme
    // (puis efface) par PreUserTrackingAction quand la piste fille demarre.
    std::map<const G4Track*, MotherInfo> fMotherInfoMap;

    std::map<const G4Track*, ReactionInfo> fReactionInfoMap;
};

#endif  // MYTRACKINGACTION_H
