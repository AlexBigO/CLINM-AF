#ifndef MYSENSITIVEDETECTOR_HH
#define MYSENSITIVEDETECTOR_HH

#include "G4AnalysisManager.hh"
#include "G4RunManager.hh"  // to get run number
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "G4VSensitiveDetector.hh"

class MySensitiveDetector : public G4VSensitiveDetector {
   public:
    MySensitiveDetector(G4String);
    ~MySensitiveDetector();

   private:
    G4double fTotalEnergyDeposited;
    void Initialize(G4HCofThisEvent*) override;
    void EndOfEvent(G4HCofThisEvent*) override;

    G4bool ProcessHits(G4Step*, G4TouchableHistory*) override;
};

#endif  // MYSENSITIVEDETECTOR_HH
