#ifndef MYPHYSICSLIST_HH
#define MYPHYSICSLIST_HH

#include "G4EmStandardPhysics.hh"
#include "G4VModularPhysicsList.hh"
#include "QGSP_INCLXX_HP.hh"

class MyPhysicsList : public G4VModularPhysicsList {
   public:
    MyPhysicsList();
    ~MyPhysicsList() = default;
};

#endif  // MYPHYSICSLIST_HH
