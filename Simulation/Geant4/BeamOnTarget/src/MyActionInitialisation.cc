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
}