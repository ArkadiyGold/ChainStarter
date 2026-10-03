// require("@nomicfoundation/hardhat-toolbox");

// /** @type import('hardhat/config').HardhatUserConfig */
// module.exports = {
//   solidity: "0.8.24",
//   networks: {
//     // Локальная нода: `npx hardhat node` (chainId 31337, http://127.0.0.1:8545)
//     localhost: {
//       url: "http://127.0.0.1:8545",
//     },
//   },
// };

require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.24",
  networks: {
    localhost: {
      url: process.env.RPC_URL || "http://127.0.0.1:8545",
    },
  },
};