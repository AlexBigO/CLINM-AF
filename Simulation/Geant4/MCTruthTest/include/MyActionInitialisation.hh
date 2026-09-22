#ifndef MYACTIONINITIALISATION_HH
#define MYACTIONINITIALISATION_HH

#include "G4VUserActionInitialization.hh"
#include "MyPrimaryGenerator.hh"
#include "MyRunAction.hh"
#include "MySteppingAction.hh"
#include "MyTrackingAction.hh"

class MyActionInitialisation : public G4VUserActionInitialization {
   public:
    MyActionInitialisation();
    ~MyActionInitialisation();

    void BuildForMaster() const override;
    void Build() const override;
};

#endif  // MYACTIONINITIALISATION_HH
