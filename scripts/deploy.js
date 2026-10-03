// const fs = require("fs");
// const path = require("path");
// const hre = require("hardhat");

// async function main() {
//   const [deployer] = await hre.ethers.getSigners();
//   console.log("Деплой с аккаунта:", deployer.address);

//   const Factory = await hre.ethers.getContractFactory("CrowdFunding");
//   const contract = await Factory.deploy();
//   await contract.waitForDeployment();

//   const address = await contract.getAddress();
//   const receipt = await contract.deploymentTransaction().wait();
//   console.log("CrowdFunding задеплоен по адресу:", address);

//   // Читаем ABI из артефакта, который создал `hardhat compile`
//   const artifact = await hre.artifacts.readArtifact("CrowdFunding");

//   const outDir = path.join(__dirname, "..", "deployments");
//   fs.mkdirSync(outDir, { recursive: true });

//   // 1) Чистый ABI (для Web3.py: json.load(...))
//   fs.writeFileSync(
//     path.join(outDir, "CrowdFunding.abi.json"),
//     JSON.stringify(artifact.abi, null, 2)
//   );

//   // 2) Адрес + блок деплоя (с него Backend начинает читать события)
//   fs.writeFileSync(
//     path.join(outDir, "contract-address.json"),
//     JSON.stringify(
//       {
//         network: hre.network.name,
//         chainId: Number((await hre.ethers.provider.getNetwork()).chainId),
//         address,
//         deployBlock: receipt.blockNumber,
//         deployer: deployer.address,
//       },
//       null,
//       2
//     )
//   );

//   console.log("Файлы для команды сохранены в папке deployments/:");
//   console.log("  - CrowdFunding.abi.json");
//   console.log("  - contract-address.json");

//   // === АВТОМАТИЧЕСКОЕ КОПИРОВАНИЕ В BACKEND ===
//   // const backendOutDir = path.join(__dirname, "..", "backend", "deployments"); 
//   // fs.mkdirSync(backendOutDir, { recursive: true });

//   // fs.copyFileSync(
//   //   path.join(outDir, "CrowdFunding.abi.json"),
//   //   path.join(backendOutDir, "CrowdFunding.abi.json")
//   // );
//   // fs.copyFileSync(
//   //   path.join(outDir, "contract-address.json"),
//   //   path.join(backendOutDir, "contract-address.json")
//   // );

//   // console.log("--> Файлы автоматически дублированы в backend/deployments/!");
// }

// main().catch((err) => {
//   console.error(err);
//   process.exitCode = 1;
// });

const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function waitForNode(retries = 30, delayMs = 2000) {
  for (let i = 0; i < retries; i++) {
    try {
      const block = await hre.ethers.provider.getBlockNumber();
      console.log(`[+] Нода доступна, блок: ${block}`);
      return;
    } catch (e) {
      console.log(`[~] Ждём ноду (${i + 1}/${retries})...`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error("Нода не поднялась за отведённое время");
}

async function main() {
  console.log("Ждём Hardhat-ноду...");
  await waitForNode();

  const [deployer] = await hre.ethers.getSigners();
  console.log("Деплой с аккаунта:", deployer.address);

  const Factory = await hre.ethers.getContractFactory("CrowdFunding");
  const contract = await Factory.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  const receipt = await contract.deploymentTransaction().wait();
  console.log("CrowdFunding задеплоен по адресу:", address);

  const artifact = await hre.artifacts.readArtifact("CrowdFunding");

  const outDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });

  fs.writeFileSync(
    path.join(outDir, "CrowdFunding.abi.json"),
    JSON.stringify(artifact.abi, null, 2)
  );

  fs.writeFileSync(
    path.join(outDir, "contract-address.json"),
    JSON.stringify(
      {
        network: hre.network.name,
        chainId: Number((await hre.ethers.provider.getNetwork()).chainId),
        address,
        deployBlock: receipt.blockNumber,
        deployer: deployer.address,
      },
      null,
      2
    )
  );

  console.log("Файлы для команды сохранены в папке deployments/");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});