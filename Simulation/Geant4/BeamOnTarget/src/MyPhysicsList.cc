#include "MyPhysicsList.hh"

MyPhysicsList::MyPhysicsList() {
    // EM physics
    RegisterPhysics(new G4EmStandardPhysics());
    // RegisterPhysics(new G4HadronPhysicsINCLXX());
}
