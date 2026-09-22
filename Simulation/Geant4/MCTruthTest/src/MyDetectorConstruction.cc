#include "MyDetectorConstruction.hh"

MyDetectorConstruction::MyDetectorConstruction() {
    // Names
    fName[kWorld] = "World";
    fName[kDetPreTarget] = "DetPreTarget";
    fName[kTarget] = "Target";
    fName[kDetPostTarget] = "DetPostTarget";

    // Set sizes
    fSize[kWorld] = G4ThreeVector{1 * m, 1 * m, 2 * m};
    fSize[kDetPreTarget] = G4ThreeVector{6. * cm, 6. * cm, 1 * mm};
    fSize[kTarget] = G4ThreeVector{6 * cm, 6 * cm, 23. * cm};
    fSize[kDetPostTarget] = G4ThreeVector{6. * cm, 6. * cm, 1 * mm};

    // Set positions
    fPos[kWorld] = G4ThreeVector{0., 0., 0.};
    fPos[kTarget] = G4ThreeVector{0., 0., 20 * cm + fSize[kTarget][2] / 2.};
    fPos[kDetPreTarget] = G4ThreeVector{
        0., 0.,
        fPos[kTarget][2] -
            (fSize[kTarget][Space::kZ] + fSize[kDetPostTarget][Space::kZ]) /
                2.};
    fPos[kDetPostTarget] = G4ThreeVector{
        0., 0.,
        fPos[kTarget][2] +
            (fSize[kTarget][Space::kZ] + fSize[kDetPostTarget][Space::kZ]) /
                2.};

    for (std::size_t iVol{0}; iVol < nVol; ++iVol) {
        fMat[iVol] = nullptr;
    }

    fNameMat[kWorld] = "G4_Galactic";
    fNameMat[kDetPreTarget] = "G4_Galactic";
    fNameMat[kTarget] = "RW3";
    fNameMat[kDetPostTarget] = "G4_Galactic";

    // NIST manager
    G4NistManager* nistManager = GetUpdatedNistManager();
    SetMaterials(nistManager);

    // Set Colors
    const auto white = G4Color(1., 1., 1., 1.);
    const auto red = G4Color(1., 0., 0., 1.);
    const auto blue = G4Color(0.56, 0.83, 1., 0.8);
    const auto green = G4Color(0., 1., 0.2, 0.5);
    fColor[kWorld] = white;
    fColor[kDetPreTarget] = blue;
    fColor[kTarget] = red;
    fColor[kDetPostTarget] = blue;
}

MyDetectorConstruction::~MyDetectorConstruction() { delete fLogicDetector; }

void MyDetectorConstruction::SetSizeBox(G4ThreeVector& sizes, G4double sizeX,
                                        G4double sizeY, G4double sizeZ) {
    sizes = G4ThreeVector{sizeX, sizeY, sizeZ};
}

/// @brief Method to set material of a volume
/// @param iVol Volume ID in Volume enumerator
/// @param nistManager Instance of G4NistManager
void MyDetectorConstruction::SetMaterial(std::size_t iVol,
                                         G4NistManager* nistManager) {
    G4Material* mat = nistManager->FindOrBuildMaterial(fNameMat[iVol]);
    if (!mat) {
        G4cerr << "Material " << fNameMat[iVol] << " undefined!" << G4endl;
        exit(1);
    }
    fMat[iVol] = mat;
    G4cerr << fMat[iVol]->GetName() << G4endl;
}

void MyDetectorConstruction::SetMaterial(G4Material*& mat,
                                         const G4String& nameMaterial,
                                         G4NistManager* nistManager) {
    mat = nistManager->FindOrBuildMaterial(nameMaterial);
    if (!mat) {
        G4cerr << "Material " << nameMaterial << " undefined!" << G4endl;
        exit(1);
    }
}

// FIXME
void MyDetectorConstruction::SetMaterials(G4NistManager* nistManager) {
    for (std::size_t iVol{0}; iVol < nVol; ++iVol) {
        SetMaterial(iVol, nistManager);
    }
}

void MyDetectorConstruction::SetSolidBox(G4VSolid*& solid,
                                         const G4String& nameSolid,
                                         G4ThreeVector& size) {
    solid = new G4Box(nameSolid, size[Space::kX] / 2., size[Space::kY] / 2.,
                      size[Space::kZ] / 2.);
}

void MyDetectorConstruction::SetSolidBox(std::size_t iVol) {
    const G4String nameSolid = "solid" + fName[iVol];
    const G4ThreeVector size = fSize[iVol];
    fSolid[iVol] = new G4Box(nameSolid, size[Space::kX] / 2.,
                             size[Space::kY] / 2., size[Space::kZ] / 2.);
}

/// @brief Method to set solid tubs with full phi coverage
/// @param iVol Volume ID in Volume enumerator
void MyDetectorConstruction::SetSolidTubs(std::size_t iVol) {
    const G4String nameSolid = "solid" + fName[iVol];
    const G4ThreeVector size = fSize[iVol];
    fSolid[iVol] =
        new G4Tubs(nameSolid, size[Space::kX] / 2., size[Space::kY] / 2.,
                   size[Space::kZ] / 2., 0.0 * deg, 360.0 * deg);
}

/// @brief Method to set logical volume
/// @param iVol Volume ID in Volume enumerator
void MyDetectorConstruction::SetLogicVol(std::size_t iVol) {
    const G4String nameLogic = "logic" + fName[iVol];
    fLogic[iVol] = new G4LogicalVolume(fSolid[iVol], fMat[iVol], nameLogic);
}

/// @brief Method to set physical volume
/// @param iVol Volume ID in Volume enumerator
/// @param iMotherVol Mother volume ID in Volume enumerator
void MyDetectorConstruction::SetPhysicVol(std::size_t iVol,
                                          std::size_t iMotherVol = kWorld) {
    const G4String namePhysic = "physic" + fName[iVol];
    G4LogicalVolume* volMother = fLogic[iMotherVol];
    if (iVol == kWorld) volMother = nullptr;

    G4RotationMatrix* rot = nullptr;

    fPhysic[iVol] =
        new G4PVPlacement(rot,           // rotation
                          fPos[iVol],    // position
                          fLogic[iVol],  // logical volume
                          "physWorld",   // name
                          volMother,     // mother volume
                          false,
                          0,  // copy number (in case of many volumes)
                          fCheckOverlaps);
}

/// @brief Method to set all volumes
void MyDetectorConstruction::SetVols() {
    std::array<std::size_t, 4> boxes{kWorld, kDetPreTarget, kTarget,
                                     kDetPostTarget};

    for (std::size_t iVol{0}; iVol < nVol; ++iVol) {
        if (std::any_of(boxes.begin(), boxes.end(),
                        [iVol](std::size_t iBox) { return iVol == iBox; })) {
            SetSolidBox(iVol);
        }

        SetLogicVol(iVol);
        if (iVol == kWorld)
            SetPhysicVol(iVol);
        else
            SetPhysicVol(iVol, kWorld);
    }
}

G4VPhysicalVolume* MyDetectorConstruction::Construct() {
    SetVols();

    // visualization parameters
    G4int iVol{0};
    for (const auto& col : fColor) {
        G4VisAttributes* visAtt = new G4VisAttributes(col);
        if (iVol != kWorld) visAtt->SetForceSolid(true);
        fLogic[iVol]->SetVisAttributes(visAtt);
        ++iVol;
    }

    return fPhysic[kWorld];
}

/// @brief Method to update NIST manager
/// @return Pointer to G4NistManager instance
G4NistManager* MyDetectorConstruction::GetUpdatedNistManager() {
    //---- Define G4NistManager instance
    G4NistManager* nistManager = G4NistManager::Instance();

    //---- Define used elements
    G4Material* Cm = nistManager->FindOrBuildMaterial("G4_C");
    G4Material* Om = nistManager->FindOrBuildMaterial("G4_O");
    G4Material* Hm = nistManager->FindOrBuildMaterial("G4_H");

    //---- Define elements
    G4double z, a;
    G4Element* H = new G4Element("Hydrogen", "H", z = 1, a = 1.008 * g / mole);
    G4Element* N = new G4Element("Nitrogen", "N", z = 7, a = 14.01 * g / mole);
    G4Element* C = new G4Element("Carbon", "C", z = 6, a = 12.00 * g / mole);
    G4Element* O = new G4Element("Oxygen", "O", z = 8, a = 16.00 * g / mole);
    G4Element* F = new G4Element("Fluor", "F", z = 9, a = 18.99 * g / mole);
    G4Element* La =
        new G4Element("Lanthanum", "La", z = 57, a = 138.91 * g / mole);
    G4Element* Ce =
        new G4Element("Cerium", "Ce", z = 58, a = 140.116 * g / mole);
    G4Element* Br =
        new G4Element("Bromide", "Br", z = 35, a = 79.904 * g / mole);
    G4Element* Ti =
        new G4Element("Titanium", "Ti", z = 22, a = 47.88 * g / mole);

    //---- Define materials
    G4double density, temperature, pressure;
    G4int ncomponents, natoms;
    G4double fractionmass;

    // CeBr3
    G4Material* CeBr3 =
        new G4Material("CeBr", density = 5.1 * g / cm3, ncomponents = 2);
    CeBr3->AddElement(Ce, natoms = 1);
    CeBr3->AddElement(Br, natoms = 3);

    // Teflon
    G4Material* PTFE =
        new G4Material("Teflon", density = 0.5 * g / cm3, ncomponents = 2);
    PTFE->AddElement(C, natoms = 2);
    PTFE->AddElement(F, natoms = 4);

    // PMMA
    // Polyméthacrylate de méthyle - (C5 H8 O2)n - C: 59.9% H: 8.0% O: 31.9%
    G4String name;
    density = 1.19 * g / cm3;
    G4Material* pmma = new G4Material(name = "PMMA", density, ncomponents = 3);
    pmma->AddMaterial(Cm, fractionmass = 59.98 * perCent);
    pmma->AddMaterial(Om, fractionmass = 31.96 * perCent);
    pmma->AddMaterial(Hm, fractionmass = 8.05 * perCent);

    G4Material* rw3 = new G4Material(name = "RW3", density = 1.045 * g / cm3,
                                     ncomponents = 4);
    rw3->AddElement(C, fractionmass = 0.9041);
    rw3->AddElement(H, fractionmass = 0.0759);
    rw3->AddElement(O, fractionmass = 0.008);
    rw3->AddElement(Ti, fractionmass = 0.012);
    // RW3: d=1.045 g/cm3 ; n=4 ; state=solid
    //         +el: name=C ; f=0.9041
    //         +el: name=H ; f=0.0759
    //         +el: name=O ; f=0.008
    //         +el: name=Ti ; f=0.012

    // Carbon
    G4Material* carbon = new G4Material(
        name = "Carbon", density = 2.27 * g / cm3, ncomponents = 1);
    carbon->AddMaterial(Cm, fractionmass = 100. * perCent);

    return nistManager;
}

// void MyDetectorConstruction::ConstructSDandField() {
//     MySensitiveDetector* sensDetPreTarget =
//         new MySensitiveDetector(fName[kDetPreTarget]);
//     MySensitiveDetector* sensDetPostTarget =
//         new MySensitiveDetector(fName[kDetPostTarget]);

//     G4SDManager::GetSDMpointer()->AddNewDetector(sensDetPreTarget);
//     G4SDManager::GetSDMpointer()->AddNewDetector(sensDetPostTarget);

//     fLogic[kDetPreTarget]->SetSensitiveDetector(sensDetPreTarget);
//     fLogic[kDetPostTarget]->SetSensitiveDetector(sensDetPostTarget);
// }