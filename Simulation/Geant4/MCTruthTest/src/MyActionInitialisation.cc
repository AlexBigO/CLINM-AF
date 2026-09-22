#include "MyActionInitialisation.hh"

MyActionInitialisation::MyActionInitialisation() {}

MyActionInitialisation::~MyActionInitialisation() {}

void MyActionInitialisation::BuildForMaster() const {
    MyRunAction* runAction = new MyRunAction();
    SetUserAction(runAction);
}

void MyActionInitialisation::Build() const {
    MyPrimaryGenerator* generator = new MyPrimaryGenerator();
    SetUserAction(generator);

    MyRunAction* runAction = new MyRunAction();
    SetUserAction(runAction);

    // TrackingAction est cree en premier : SteppingAction a besoin d'un
    // pointeur vers elle pour lui transmettre l'info sur la particule mere.
    auto trackingAction = new MyTrackingAction();
    SetUserAction(trackingAction);
    SetUserAction(new MySteppingAction(trackingAction));
}