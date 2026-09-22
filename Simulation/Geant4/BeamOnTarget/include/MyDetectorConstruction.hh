#ifndef MYDETECTORCONSTRUCTION_HH
#define MYDETECTORCONSTRUCTION_HH

#include <array>

#include "G4Box.hh"
#include "G4Color.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4Tubs.hh"
#include "G4UnitsTable.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4VisAttributes.hh"
#include "MySensitiveDetector.hh"

enum Space : std::size_t { kX = 0, kY, kZ, nDims };

enum Volume : std::size_t {
    kWorld = 0,
    kDetPreTarget,
    kTarget,
    kDetPostTarget,
    nVol
};

class MyDetectorConstruction : public G4VUserDetectorConstruction {
   public:
    MyDetectorConstruction();
    ~MyDetectorConstruction() override;

    G4VPhysicalVolume* Construct() override;

   public:
    G4NistManager* GetUpdatedNistManager();
    void SetMaterials(G4NistManager*);              // FIXME
    void SetMaterial(std::size_t, G4NistManager*);  // FIXME
    void SetMaterial(G4Material*&, const G4String&, G4NistManager*);
    void SetSizeBox(G4ThreeVector&, G4double, G4double, G4double);
    void SetSolidBox(std::size_t);
    void SetSolidBox(G4VSolid*&, const G4String&, G4ThreeVector&);
    void SetSolidTubs(std::size_t);

    void SetLogicVol(std::size_t);
    void SetPhysicVol(std::size_t, std::size_t);

    void SetVols();

   private:
    static constexpr bool fCheckOverlaps = true;

    // Materials
    std::array<G4Material*, nVol> fMat;
    std::array<G4String, nVol> fNameMat;

    // Volumes
    std::array<G4String, nVol> fName;
    // Solid volumes
    std::array<G4VSolid*, nVol> fSolid;
    std::array<G4ThreeVector, nVol> fSize;
    // Logical volumes
    std::array<G4LogicalVolume*, nVol> fLogic;
    // Physical volumes
    std::array<G4VPhysicalVolume*, nVol> fPhysic;
    std::array<G4ThreeVector, nVol> fPos;

    // Colors
    std::array<G4Color, nVol> fColor;
    // VisAttributes
    // std::array<G4VisAttributes*, nVol> fVisAtt;
    // World
    // G4Material* fMatWorld = nullptr;
    // G4VSolid* fSolidWorld = nullptr;
    // G4LogicalVolume* fLogicWorld = nullptr;
    // G4VPhysicalVolume* fPhysicWorld = nullptr;
    // G4ThreeVector fSizeWorld{};
    // G4ThreeVector fPosWorld{};

    // // Plastic 1
    // G4Material* fMatPlastic1 = nullptr;
    // G4VSolid* fSolidPlastic1 = nullptr;
    // G4LogicalVolume* fLogicPlastic1 = nullptr;
    // G4VPhysicalVolume* fPhysicPlastic1 = nullptr;
    // G4ThreeVector fSizePlastic1{};
    // G4ThreeVector fPosPlastic1{};

    G4LogicalVolume* fLogicDetector = nullptr;

    void ConstructSDandField() override;
};

#endif  // MYDETECTORCONSTRUCTION_HH
