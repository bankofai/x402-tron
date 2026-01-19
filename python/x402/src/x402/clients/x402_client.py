"""
X402Client - x402 协议的核心支付客户端
"""

import logging
from typing import Any, Callable, Protocol

from x402.types import (
    PaymentPayload,
    PaymentPermitContext,
    PaymentRequirements,
)

logger = logging.getLogger(__name__)


class ClientMechanism(Protocol):
    """客户端机制接口"""

    def scheme(self) -> str:
        """获取支付方案名称"""
        ...

    async def create_payment_payload(
        self,
        requirements: PaymentRequirements,
        resource: str,
        extensions: dict[str, Any] | None = None,
    ) -> PaymentPayload:
        """创建支付载荷"""
        ...


PaymentRequirementsSelector = Callable[[list[PaymentRequirements]], PaymentRequirements]


class PaymentRequirementsFilter:
    """选择支付要求的过滤选项"""

    def __init__(
        self,
        scheme: str | None = None,
        network: str | None = None,
        max_amount: str | None = None,
    ):
        self.scheme = scheme
        self.network = network
        self.max_amount = max_amount


class MechanismEntry:
    """已注册的机制条目"""

    def __init__(self, pattern: str, mechanism: ClientMechanism, priority: int):
        self.pattern = pattern
        self.mechanism = mechanism
        self.priority = priority


class X402Client:
    """
    x402 协议的核心支付客户端。

    管理支付机制注册表并协调支付流程。
    """

    def __init__(self) -> None:
        self._mechanisms: list[MechanismEntry] = []

    def register(self, network_pattern: str, mechanism: ClientMechanism) -> "X402Client":
        """
        为网络模式注册支付机制。

        参数:
            network_pattern: 网络模式（例如 "eip155:*", "tron:shasta"）
            mechanism: 支付机制实例

        返回:
            self 以支持链式调用
        """
        priority = self._calculate_priority(network_pattern)
        logger.info(f"Registering mechanism for pattern '{network_pattern}' with priority {priority}")
        self._mechanisms.append(MechanismEntry(network_pattern, mechanism, priority))
        self._mechanisms.sort(key=lambda e: e.priority, reverse=True)
        return self

    def select_payment_requirements(
        self,
        accepts: list[PaymentRequirements],
        filters: PaymentRequirementsFilter | None = None,
    ) -> PaymentRequirements:
        """
        从可用选项中选择支付要求。

        参数:
            accepts: 可用的支付要求
            filters: 可选过滤器

        返回:
            选定的支付要求

        异常:
            ValueError: 未找到支持的支付要求
        """
        logger.info(f"Selecting payment requirements from {len(accepts)} options")
        logger.debug(f"Available payment requirements: {[r.model_dump() for r in accepts]}")
        
        candidates = list(accepts)

        if filters:
            logger.debug(f"Applying filters: scheme={filters.scheme}, network={filters.network}, max_amount={filters.max_amount}")
            if filters.scheme:
                candidates = [r for r in candidates if r.scheme == filters.scheme]
                logger.debug(f"After scheme filter: {len(candidates)} candidates")
            if filters.network:
                candidates = [r for r in candidates if r.network == filters.network]
                logger.debug(f"After network filter: {len(candidates)} candidates")
            if filters.max_amount:
                max_val = int(filters.max_amount)
                candidates = [r for r in candidates if int(r.amount) <= max_val]
                logger.debug(f"After amount filter: {len(candidates)} candidates")

        candidates = [r for r in candidates if self._find_mechanism(r.network) is not None]
        logger.debug(f"After mechanism filter: {len(candidates)} candidates")

        if not candidates:
            logger.error("No supported payment requirements found")
            raise ValueError("No supported payment requirements found")

        selected = candidates[0]
        logger.info(f"Selected payment requirement: network={selected.network}, scheme={selected.scheme}, amount={selected.amount}")
        return selected

    async def create_payment_payload(
        self,
        requirements: PaymentRequirements,
        resource: str,
        extensions: dict[str, Any] | None = None,
    ) -> PaymentPayload:
        """
        为给定要求创建支付载荷。

        参数:
            requirements: 选定的支付要求
            resource: 资源 URL
            extensions: 可选扩展

        返回:
            支付载荷
        """
        logger.info(f"Creating payment payload for network={requirements.network}, resource={resource}")
        mechanism = self._find_mechanism(requirements.network)
        if mechanism is None:
            logger.error(f"No mechanism registered for network: {requirements.network}")
            raise ValueError(f"No mechanism registered for network: {requirements.network}")

        logger.debug(f"Using mechanism: {mechanism.__class__.__name__}")
        payload = await mechanism.create_payment_payload(requirements, resource, extensions)
        logger.info("Payment payload created successfully")
        return payload

    async def handle_payment(
        self,
        accepts: list[PaymentRequirements],
        resource: str,
        extensions: dict[str, Any] | None = None,
        selector: PaymentRequirementsSelector | None = None,
    ) -> PaymentPayload:
        """
        处理需要支付的响应。

        参数:
            accepts: 可用的支付要求
            resource: 资源 URL
            extensions: 可选扩展
            selector: 可选自定义选择器

        返回:
            支付载荷
        """
        if selector:
            requirements = selector(accepts)
        else:
            requirements = self.select_payment_requirements(accepts)

        return await self.create_payment_payload(requirements, resource, extensions)

    def _find_mechanism(self, network: str) -> ClientMechanism | None:
        """查找网络的机制"""
        for entry in self._mechanisms:
            if self._match_pattern(entry.pattern, network):
                return entry.mechanism
        return None

    def _match_pattern(self, pattern: str, network: str) -> bool:
        """将网络与模式匹配"""
        if pattern == network:
            return True
        if pattern.endswith(":*"):
            prefix = pattern[:-1]
            return network.startswith(prefix)
        return False

    def _calculate_priority(self, pattern: str) -> int:
        """计算模式的优先级（更具体 = 更高优先级）"""
        if pattern.endswith(":*"):
            return 1
        return 10
