const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  // Загружаем адрес задеплоенного контракта
  const addrPath = path.join(__dirname, "..", "deployments", "contract-address.json");
  const { address } = JSON.parse(fs.readFileSync(addrPath, "utf8"));

  const [signer] = await hre.ethers.getSigners();
  const CrowdFunding = await hre.ethers.getContractFactory("CrowdFunding");
  const contract = CrowdFunding.attach(address);

  console.log(`Отправляем транзакцию на контракт: ${address}...`);

  // Вызываем функцию создания кампании (goal: 1 ETH, duration: 7 дней = 604800 сек)
  const goal = hre.ethers.parseEther("1.0");
  const duration = 7 * 24 * 60 * 60;
  
  const tx = await contract.createCampaign(goal, duration);
  await tx.wait();

  console.log("Успех! Кампания создана, событие CampaignCreated отправлено в сеть.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});