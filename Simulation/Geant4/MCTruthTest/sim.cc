#include <iostream>

#include "G4RunManagerFactory.hh"
#include "G4UIExecutive.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4VisManager.hh"
#include "MyActionInitialisation.hh"
#include "MyDetectorConstruction.hh"
#include "QGSP_BIC.hh"
#include "QGSP_INCLXX_HP.hh"

int main(int argc, char** argv) {
    G4UIExecutive* ui = nullptr;
    // Visual manager
    if (argc == 1) {  // interactive mode
        ui = new G4UIExecutive(argc, argv);
    }

    // RunManager
    // controls the flow of the program and manages the event loop(s) within a
    // run
    auto runManager = G4RunManagerFactory::CreateRunManager();

    // Detector construction
    runManager->SetUserInitialization(new MyDetectorConstruction());
    // Physics list
    // runManager->SetUserInitialization(new MyPhysicsList());
    G4VModularPhysicsList* physicsList =
        new QGSP_BIC();  // new QGSP_INCLXX_HP();  // new QBBC();
    physicsList->SetVerboseLevel(0);
    runManager->SetUserInitialization(physicsList);
    // Action initialization
    runManager->SetUserInitialization(new MyActionInitialisation());

    G4VisManager* visManager = new G4VisExecutive(argc, argv);
    visManager->Initialize();

    G4UImanager* uiManager = G4UImanager::GetUIpointer();
    // Question: what is the difference between GetUIpointer and
    // GetMasterUIpointer?

    if (ui) {  // interactive mode
        uiManager->ApplyCommand("/control/execute visDefault.mac");
        ui->SessionStart();
    } else {  // batch mode
        G4String command = "/control/execute ";
        G4String nameFile = argv[1];
        uiManager->ApplyCommand(command + nameFile);
    }

    // release memory
    delete ui;
    delete visManager;
    delete runManager;
    return 0;
}