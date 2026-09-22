#ifndef MYSTEPPINGACTION_H
#define MYSTEPPINGACTION_H

#include "G4UserSteppingAction.hh"

class G4Step;
class MyTrackingAction;

// A chaque step, on regarde si la piste courante ("la mere") a produit
// des secondaires PENDANT ce step. Si oui, on transmet a TrackingAction
// l'identite de la mere (nom, PDG) et son energie cinetique JUSTE APRES
// avoir cree ces secondaires -- c'est la seule maniere d'obtenir cette
// information, puisqu'au moment ou TrackingAction traite la piste fille,
// la mere a deja fini d'etre trackee (son objet G4Track n'existe plus).
class MySteppingAction : public G4UserSteppingAction {
   public:
    explicit MySteppingAction(MyTrackingAction* trackingAction);
    ~MySteppingAction() override;

    void UserSteppingAction(const G4Step* step) override;

   private:
    MyTrackingAction* fTrackingAction = nullptr;
};

#endif  // MYSTEPPINGACTION_H
