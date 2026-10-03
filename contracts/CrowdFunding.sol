// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ChainStarter — простой краудфандинг "всё или ничего"
/// @notice Создатель ставит цель (goal) и срок (deadline).
///         Если к дедлайну цель собрана — создатель забирает деньги (claim).
///         Если нет — каждый спонсор может вернуть свой вклад (refund).
contract CrowdFunding {
    // ---------------------------------------------------------------------
    // Данные
    // ---------------------------------------------------------------------

    struct Campaign {
        address creator;   // кто создал кампанию
        uint256 goal;      // цель сбора, в wei
        uint256 deadline;  // unix-время окончания сбора
        uint256 raised;    // сколько собрано, в wei
        bool claimed;      // забрал ли создатель деньги
    }

    /// @notice Сколько кампаний создано (id идут с 1 до campaignCount)
    uint256 public campaignCount;

    /// @notice id => кампания
    mapping(uint256 => Campaign) public campaigns;

    /// @notice id => адрес спонсора => сколько он внёс
    mapping(uint256 => mapping(address => uint256)) public contributions;

    // ---------------------------------------------------------------------
    // События (их будет слушать Backend через Web3.py)
    // ---------------------------------------------------------------------

    event CampaignCreated(
        uint256 indexed campaignId,
        address indexed creator,
        uint256 goal,
        uint256 deadline
    );

    event Contributed(
        uint256 indexed campaignId,
        address indexed contributor,
        uint256 amount
    );

    event Refunded(
        uint256 indexed campaignId,
        address indexed contributor,
        uint256 amount
    );

    event FundsClaimed(
        uint256 indexed campaignId,
        address indexed creator,
        uint256 amount
    );

    // ---------------------------------------------------------------------
    // Функции
    // ---------------------------------------------------------------------

    /// @notice Создать кампанию
    /// @param goal     цель в wei (> 0)
    /// @param duration длительность сбора в секундах (> 0)
    /// @return id      номер новой кампании
    function createCampaign(uint256 goal, uint256 duration) external returns (uint256 id) {
        require(goal > 0, "Goal must be > 0");
        require(duration > 0, "Duration must be > 0");

        id = ++campaignCount;
        uint256 deadline = block.timestamp + duration;

        campaigns[id] = Campaign({
            creator: msg.sender,
            goal: goal,
            deadline: deadline,
            raised: 0,
            claimed: false
        });

        emit CampaignCreated(id, msg.sender, goal, deadline);
    }

    /// @notice Внести деньги в кампанию (пока не наступил дедлайн)
    function fund(uint256 id) external payable {
        Campaign storage c = campaigns[id];
        require(c.creator != address(0), "Campaign does not exist");
        require(block.timestamp < c.deadline, "Campaign ended");
        require(msg.value > 0, "Send some ETH");

        c.raised += msg.value;
        contributions[id][msg.sender] += msg.value;

        emit Contributed(id, msg.sender, msg.value);
    }

    /// @notice Вернуть свой вклад, если кампания провалилась
    function refund(uint256 id) external {
        Campaign storage c = campaigns[id];
        require(c.creator != address(0), "Campaign does not exist");
        require(block.timestamp >= c.deadline, "Campaign still active");
        require(c.raised < c.goal, "Goal reached, no refunds");

        uint256 amount = contributions[id][msg.sender];
        require(amount > 0, "Nothing to refund");

        // Сначала обнуляем баланс, потом шлём деньги (защита от reentrancy)
        contributions[id][msg.sender] = 0;

        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "Transfer failed");

        emit Refunded(id, msg.sender, amount);
    }

    /// @notice Забрать собранные деньги, если цель достигнута
    function claim(uint256 id) external {
        Campaign storage c = campaigns[id];
        require(c.creator != address(0), "Campaign does not exist");
        require(msg.sender == c.creator, "Only creator");
        require(block.timestamp >= c.deadline, "Campaign still active");
        require(c.raised >= c.goal, "Goal not reached");
        require(!c.claimed, "Already claimed");

        // Сначала помечаем, потом шлём деньги
        c.claimed = true;
        uint256 amount = c.raised;

        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "Transfer failed");

        emit FundsClaimed(id, msg.sender, amount);
    }
}
