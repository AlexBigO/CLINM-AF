#include "MyPrimaryGenerator.hh"

MyPrimaryGenerator::MyPrimaryGenerator() {
    fParticleGun = new G4ParticleGun(1);
    // fGeneralParticleSource = new G4GeneralParticleSource();

    // particle position
    G4double x = 0. * m;
    G4double y = 0. * m;
    G4double z = 0. * m;

    G4ThreeVector pos(x, y, z);

    // particle direction
    G4double px = 0.;
    G4double py = 0.;
    G4double pz = 1;

    G4ThreeVector momDirection(px, py, pz);  // G4ParticleMomentum

    // particle type
    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
    G4ParticleDefinition* particle = particleTable->FindParticle("proton");

    fParticleGun->SetParticlePosition(pos);
    fParticleGun->SetParticleMomentumDirection(momDirection);
    fParticleGun->SetParticleEnergy(100. * MeV);
    fParticleGun->SetParticleDefinition(particle);

    // fGeneralParticleSource->SetParticlePosition(pos);
    // fGeneralParticleSource->SetParticleDefinition(particle);
}

MyPrimaryGenerator::~MyPrimaryGenerator() {
    delete fParticleGun;
    fParticleGun = nullptr;
    // delete fGeneralParticleSource;
    // fGeneralParticleSource = nullptr;
}

void MyPrimaryGenerator::GeneratePrimaries(G4Event* event) {
    // create vertex
    fParticleGun->GeneratePrimaryVertex(event);
    // fGeneralParticleSource->GeneratePrimaryVertex(event);
}