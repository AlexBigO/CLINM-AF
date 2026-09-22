#ifndef MYRUNACTION_HH
#define MYRUNACTION_HH

#include "G4AnalysisManager.hh"
#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "G4UserRunAction.hh"

class MyRunAction : public G4UserRunAction {
   public:
    MyRunAction();
    ~MyRunAction();

    void BeginOfRunAction(const G4Run*) override;
    void EndOfRunAction(const G4Run*) override;
};

#endif  // MYRUNACTION_HH
