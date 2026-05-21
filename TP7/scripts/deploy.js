import hre from "hardhat";

async function main() {
    const connection = await hre.network.connect();

    const Factory = await connection.ethers.getContractFactory("CFPFactory");

    const factory = await Factory.deploy();

    await factory.waitForDeployment();

    console.log("CFPFactory deployed to:", await factory.getAddress());
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});