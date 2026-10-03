const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("CrowdFunding", function () {
  const GOAL = ethers.parseEther("10");
  const DURATION = 7 * 24 * 60 * 60; // 7 дней

  let contract, creator, alice, bob;

  beforeEach(async function () {
    [creator, alice, bob] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("CrowdFunding");
    contract = await Factory.deploy();
    await contract.waitForDeployment();
  });

  // Тест 1: создание кампании
  it("создаёт кампанию и эмитит CampaignCreated", async function () {
    await expect(contract.connect(creator).createCampaign(GOAL, DURATION))
      .to.emit(contract, "CampaignCreated");

    const c = await contract.campaigns(1);
    expect(c.creator).to.equal(creator.address);
    expect(c.goal).to.equal(GOAL);
    expect(c.raised).to.equal(0n);
    expect(await contract.campaignCount()).to.equal(1n);
  });

  // Тест 2: вклад
  it("принимает вклад и эмитит Contributed", async function () {
    await contract.createCampaign(GOAL, DURATION);
    const amount = ethers.parseEther("3");

    await expect(contract.connect(alice).fund(1, { value: amount }))
      .to.emit(contract, "Contributed")
      .withArgs(1, alice.address, amount);

    expect((await contract.campaigns(1)).raised).to.equal(amount);
    expect(await contract.contributions(1, alice.address)).to.equal(amount);
  });

  // Тест 3: успех -> создатель забирает деньги
  it("если цель собрана — создатель забирает деньги (FundsClaimed)", async function () {
    await contract.connect(creator).createCampaign(GOAL, DURATION);
    await contract.connect(alice).fund(1, { value: ethers.parseEther("6") });
    await contract.connect(bob).fund(1, { value: ethers.parseEther("5") });

    await time.increase(DURATION + 1);

    await expect(contract.connect(creator).claim(1))
      .to.changeEtherBalances(
        [creator, contract],
        [ethers.parseEther("11"), -ethers.parseEther("11")]
      );

    // повторно забрать нельзя
    await expect(contract.connect(creator).claim(1)).to.be.revertedWith("Already claimed");
  });

  it("claim эмитит FundsClaimed", async function () {
    await contract.connect(creator).createCampaign(GOAL, DURATION);
    await contract.connect(alice).fund(1, { value: GOAL });
    await time.increase(DURATION + 1);

    await expect(contract.connect(creator).claim(1))
      .to.emit(contract, "FundsClaimed")
      .withArgs(1, creator.address, GOAL);
  });

  // Тест 4: провал -> спонсоры получают деньги назад
  it("если цель не собрана — спонсор возвращает вклад (Refunded)", async function () {
    await contract.connect(creator).createCampaign(GOAL, DURATION);
    const amount = ethers.parseEther("2");
    await contract.connect(alice).fund(1, { value: amount });

    await time.increase(DURATION + 1);

    await expect(contract.connect(alice).refund(1))
      .to.emit(contract, "Refunded")
      .withArgs(1, alice.address, amount);

    // повторный возврат невозможен
    await expect(contract.connect(alice).refund(1)).to.be.revertedWith("Nothing to refund");
    // и деньги на контракте не «застряли»
    expect(await ethers.provider.getBalance(await contract.getAddress())).to.equal(0n);
  });

  // Тест 5: защита денег
  it("не даёт украсть или потерять деньги (запрещённые действия)", async function () {
    await contract.connect(creator).createCampaign(GOAL, DURATION);
    await contract.connect(alice).fund(1, { value: ethers.parseEther("4") });

    // до дедлайна нельзя ни claim, ни refund
    await expect(contract.connect(creator).claim(1)).to.be.revertedWith("Campaign still active");
    await expect(contract.connect(alice).refund(1)).to.be.revertedWith("Campaign still active");

    await time.increase(DURATION + 1);

    // цель не достигнута -> claim запрещён
    await expect(contract.connect(creator).claim(1)).to.be.revertedWith("Goal not reached");
    // после дедлайна вносить нельзя
    await expect(contract.connect(bob).fund(1, { value: 1 })).to.be.revertedWith("Campaign ended");
  });

  it("при успехе refund запрещён, а claim доступен только создателю", async function () {
    await contract.connect(creator).createCampaign(GOAL, DURATION);
    await contract.connect(alice).fund(1, { value: GOAL });
    await time.increase(DURATION + 1);

    await expect(contract.connect(alice).refund(1)).to.be.revertedWith("Goal reached, no refunds");
    await expect(contract.connect(alice).claim(1)).to.be.revertedWith("Only creator");
  });

  it("отклоняет неверные входные данные", async function () {
    await expect(contract.createCampaign(0, DURATION)).to.be.revertedWith("Goal must be > 0");
    await expect(contract.createCampaign(GOAL, 0)).to.be.revertedWith("Duration must be > 0");
    await expect(contract.connect(alice).fund(99, { value: 1 })).to.be.revertedWith("Campaign does not exist");

    await contract.createCampaign(GOAL, DURATION);
    await expect(contract.connect(alice).fund(1, { value: 0 })).to.be.revertedWith("Send some ETH");
  });
});
