import { ethers } from "hardhat";

async function main() {
  // Obtener el contrato
  const TaskBoard = await ethers.getContractFactory("TaskBoard");

  // Desplegar
  const taskBoard = await TaskBoard.deploy();

  // Esperar a que se mine
  await taskBoard.waitForDeployment();

  // Obtener dirección
  const address = await taskBoard.getAddress();

  console.log("TaskBoard deployed at:", address);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});