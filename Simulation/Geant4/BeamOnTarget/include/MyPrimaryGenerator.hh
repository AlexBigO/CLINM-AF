#ifndef MYPRIMARYGENERATOR_HH
#define MYPRIMARYGENERATOR_HH

#include "G4Event.hh"
#include "G4GeneralParticleSource.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4VUserPrimaryGeneratorAction.hh"

class MyPrimaryGenerator : public G4VUserPrimaryGeneratorAction {
   public:
    MyPrimaryGenerator();
    ~MyPrimaryGenerator();

    void GeneratePrimaries(G4Event*) override;

   private:
    // G4GeneralParticleSource* fGeneralParticleSource = nullptr;
    G4ParticleGun* fParticleGun = nullptr;
};

#endif  // MYPRIMARYGENERATOR_HH
