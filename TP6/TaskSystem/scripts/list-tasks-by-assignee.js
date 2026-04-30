#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ethers } from "ethers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DEFAULT_RPC_URL = "http://localhost:8545";
const VALID_STATES = new Set(["pending", "in-progress", "done"]);
const VALID_TIMESTAMP_MODES = new Set(["contract", "events"]);

function printUsageAndExit(message) {
  if (message) {
    console.error(`Error: ${message}`);
  }

  console.error(`
Usage:
  node scripts/list-tasks-by-assignee.js \
    --board <task_board_address> \
    --assignee <address> \
    --state <pending|in-progress|done> \
    --timestamps <contract|events> \
    [--rpc <uri>]

Examples:
  node scripts/list-tasks-by-assignee.js \
    --board 0x1234...abcd \
    --assignee 0xabcd...1234 \
    --state pending \
    --timestamps contract

  node scripts/list-tasks-by-assignee.js \
    --board 0x1234...abcd \
    --assignee 0xabcd...1234 \
    --state done \
    --timestamps events \
    --rpc http://localhost:8545
`);

  process.exit(1);
}

function parseArgs(argv) {
  const args = {
    rpc: DEFAULT_RPC_URL,
  };

  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];

    if (!token.startsWith("--")) {
      continue;
    }

    const key = token.slice(2);
    const value = argv[i + 1];

    if (!value || value.startsWith("--")) {
      printUsageAndExit(`Missing value for argument '${token}'`);
    }

    args[key] = value;
    i += 1;
  }

  if (!args.board) {
    printUsageAndExit("Argument '--board' is required");
  }

  if (!args.assignee) {
    printUsageAndExit("Argument '--assignee' is required");
  }

  if (!args.state || !VALID_STATES.has(args.state)) {
    printUsageAndExit("Argument '--state' must be one of: pending, in-progress, done");
  }

  if (!args.timestamps || !VALID_TIMESTAMP_MODES.has(args.timestamps)) {
    printUsageAndExit("Argument '--timestamps' must be one of: contract, events");
  }

  if (!ethers.isAddress(args.board)) {
    printUsageAndExit("'--board' is not a valid Ethereum address");
  }

  if (!ethers.isAddress(args.assignee)) {
    printUsageAndExit("'--assignee' is not a valid Ethereum address");
  }

  return args;
}

function loadArtifactJson(relativePath) {
  const artifactPath = path.join(__dirname, "..", relativePath);
  const raw = fs.readFileSync(artifactPath, "utf8");
  return JSON.parse(raw);
}

/**
 * Obtiene la lista de tareas de un responsable asignado para un estado dado.
 *
 * Especificación:
 * - Entrada:
 *   - taskBoardContract: instancia ethers de TaskBoard ya construida.
 *   - taskContractFactory: función que recibe la dirección de una Task y devuelve
 *     su contrato ethers ya conectado al mismo provider.
 *   - assignee: dirección del responsable asignado a consultar.
 *   - state: "pending" | "in-progress" | "done".
 *   - timestampSource: "contract" | "events".
 * - Salida:
 *   - Promise<Array<{ taskAddress: string, description: string, timestamps: object }>>
 * - Errores:
 *   - Lanza error si faltan dependencias requeridas.
 *   - Lanza error si no hay contrato desplegado en la dirección de TaskBoard
 *     para el provider configurado.
 */
async function listTasksByAssignee({
  taskBoardContract,
  taskContractFactory,
  assignee,
  state,
  timestampSource,
}) {
  // TODO (estudiante): implementar validaciones de entrada.
  if (!taskBoardContract) throw new Error("taskBoardContract requerido");
  if (!taskContractFactory) throw new Error("taskContractFactory requerido");
  if (!assignee) throw new Error("assignee requerido");
  if (!state) throw new Error("state requerido");
  if (!timestampSource) throw new Error("timestampSource requerido");

  const provider = taskBoardContract.runner.provider;
  const code = await provider.getCode(await taskBoardContract.getAddress());
  if (code === "0x") {
    throw new Error("No hay contrato desplegado en la direccion indicada");
  }

  // TODO (estudiante): implementar consulta por estado, armado de contratos Task
  // y resolucion de timestamps por contrato o por eventos.

  let taskAddresses = [];

  if (state === "pending") {
    taskAddresses = await taskBoardContract.todoByAssignee(assignee);
  } else if (state === "in-progress") {
    taskAddresses = await taskBoardContract.inProgressByAssignee(assignee);
  } else if (state === "done") {
    taskAddresses = await taskBoardContract.doneByAssignee(assignee);
  }

  const results = [];

  for (const address of taskAddresses) {
    const task = taskContractFactory(address);

    const description = await task.description();

    let timestamps = {};

    if (timestampSource === "contract") {
      const assignedAt = await task.assignedAt();
      const startedAt = await task.startedAt();
      const completedAt = await task.completedAt();

      if (assignedAt > 0n) {
        timestamps.assignedAt = new Date(Number(assignedAt) * 1000).toISOString();
      }

      if (state !== "pending" && startedAt > 0n) {
        timestamps.startedAt = new Date(Number(startedAt) * 1000).toISOString();
      }

      if (state === "done" && completedAt > 0n) {
        timestamps.completedAt = new Date(Number(completedAt) * 1000).toISOString();
      }
    }

    if (timestampSource === "events") {
      const provider = taskBoardContract.runner.provider;

      const assignedEvents = await task.queryFilter(
        task.filters.TaskAssigned(null, null)
      );
      if (assignedEvents.length > 0) {
        const block = await provider.getBlock(assignedEvents[0].blockNumber);
        timestamps.assignedAt = new Date(block.timestamp * 1000).toISOString();
      }

      if (state !== "pending") {
        const startedEvents = await task.queryFilter(
          task.filters.TaskStarted(null)
        );
        if (startedEvents.length > 0) {
          const block = await provider.getBlock(startedEvents[0].blockNumber);
          timestamps.startedAt = new Date(block.timestamp * 1000).toISOString();
        }
      }

      if (state === "done") {
        const completedEvents = await task.queryFilter(
          task.filters.TaskCompleted(null)
        );
        if (completedEvents.length > 0) {
          const block = await provider.getBlock(completedEvents[0].blockNumber);
          timestamps.completedAt = new Date(block.timestamp * 1000).toISOString();
        }
      }
    }

    results.push({
      taskAddress: address,
      description,
      timestamps,
    });
  }

  return results;
}

// Punto de entrada CLI: parsea argumentos, arma contratos/factorías
// y escribe en stdout un JSON con los resultados de la consulta.
async function main() {
  const args = parseArgs(process.argv.slice(2));

  const taskBoardArtifact = loadArtifactJson(path.join("artifacts", "contracts", "TaskBoard.sol", "TaskBoard.json"));
  const taskArtifact = loadArtifactJson(path.join("artifacts", "contracts", "Task.sol", "Task.json"));

  const provider = new ethers.JsonRpcProvider(args.rpc);
  const taskBoardContract = new ethers.Contract(args.board, taskBoardArtifact.abi, provider);
  const taskContractFactory = (taskAddress) => new ethers.Contract(taskAddress, taskArtifact.abi, provider);

  const tasks = await listTasksByAssignee({
    taskBoardContract,
    taskContractFactory,
    assignee: args.assignee,
    state: args.state,
    timestampSource: args.timestamps,
  });

  const output = {
    rpc: args.rpc,
    board: args.board,
    assignee: args.assignee,
    state: args.state,
    timestampSource: args.timestamps,
    count: tasks.length,
    tasks,
  };

  console.log(JSON.stringify(output, null, 2));
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  main().catch((error) => {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  });
}

export {
  listTasksByAssignee,
};