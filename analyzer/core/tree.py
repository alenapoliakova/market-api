from datetime import datetime
from uuid import UUID


class MarketTree:

    def __init__(self):
        self.nodes = {}
        self.price_by_id = {}

    def add_price(self, id: UUID, date: datetime, price: int):
        """Добавление цены товара в словарик по ID товара.

        Parameters:
            id (UUID):
                Уникальный идентификатор товара.
            date (datetime):
                Время обновления цены товара.
            price (int):
                Стоимость товара.

        Returns:
            None
        """
        if id not in self.price_by_id:
            self.price_by_id[id] = [(date, price)]
        else:
            self.price_by_id[id].append((date, price))

    def delete_price_by_id(self, id: UUID):
        """Удаление истории стоимости товара по ID товара.

        Parameters:
            id (UUID):
                Уникальный идентификатор товара.

        Returns:
            None
        """
        del self.price_by_id[id]

    def add(self, node: dict) -> None:
        """Добавление товара / категории в дерево Маркета.

        Parameters:
            node (dict):
                Словарь из информации о товаре / категории.

        Returns:
            None
        """
        id = node["id"]
        parent_id = node["parent_id"]

        child = [] if node["type"].value == "CATEGORY" else None
        self.nodes[id] = node | {"children": self.nodes.get(id, {}).get("children", child)}

        if node["price"]:
            self.add_price(id, node["date"], node["price"])
        elif node["type"].value == "CATEGORY":
            for node_id, node_info in self.nodes.items():
                if node_info["parent_id"] == id and node_id not in self.nodes[id]["children"]:
                    self.nodes[id]["children"].append(node_id)

        if parent_id in self.nodes and id not in self.nodes[parent_id]["children"]:
            self.nodes[parent_id]["children"].append(id)

    def delete_node_by_id(self, id: UUID) -> dict | None:
        """Удаление товара / категории по ID. При удалении категории удаляются все дети данной категории.

        Parameters:
            id (UUID):
                Уникальный идентификатор товара / категории.

        Returns:
            node (dict | NoneType):
                Информация об удалённом элементе. Если данного элемента нет в Маркете, то вернётся None.
        """
        if id in self.nodes:
            node = self.nodes[id]
            parent_id = node["parent_id"]
            if parent_id and parent_id in self.nodes:
                self.nodes[parent_id]["children"].remove(id)
            del self.nodes[id]
            return node

    def show(self, id: UUID, level=0) -> None:
        """Метод для вывода в консоль визуального представления товаров / категорий по ID.

        Parameters:
            id (UUID):
                Уникальный идентификатор товара / категории.
            level (int):
                Уровень в каталоге.

        Returns:
            None
        """
        children = self.nodes[id]["children"]
        print("  " * level, f"{self.nodes[id]['name']} (id={id})")
        level += 1

        for node in children:
            self.show(node["id"], level)

    def calculate_price_for_category(self, id: UUID) -> tuple[int, int]:
        """Метод для вычисления общей цены и количества товаров в категории по ID категории.

        Parameters:
            id (UUID):
                Уникальный идентификатор категории.

        Returns:
            amount, price (tuple):
                Кортеж из общей цены в категории и количество товаров в ней.
        """
        amount = 0
        count_items = 0
        for node_id in self.nodes[id]["children"]:
            if self.nodes[node_id]["type"].value == "OFFER":
                amount += self.nodes[node_id]["price"]
                count_items += 1
            elif self.nodes[node_id]["type"].value == "CATEGORY":
                a, c = self.calculate_price_for_category(node_id)
                amount += a
                count_items += c
        return amount, count_items

    def calculate_date_for_category(self, id: UUID) -> datetime:
        """Метод для вычисления последней даты обновления товаров / категорий в конкретной категории по ID.

        Parameters:
            id (UUID):
                Уникальный идентификатор категории.

        Returns:
            date (datetime):
                Дата последнего обновления.
        """
        date = self.nodes[id]["date"]
        for node_id in self.nodes[id]["children"]:
            if self.nodes[node_id]["type"].value == "OFFER":
                if self.nodes[node_id]["date"] > date:
                    date = self.nodes[node_id]["date"]
            elif self.nodes[node_id]["type"].value == "CATEGORY":
                new_date = self.calculate_date_for_category(node_id)
                if new_date > date:
                    date = new_date
        return date

    @staticmethod
    def convert_date(date: datetime) -> str:
        """Конвертация даты в определённый формат.
        Пример конвертации: 2022-02-03T12:00:00+00:00 -> 2022-02-03T12:00:00Z.

        Parameters:
            date (datetime):
                Время обновления товара / категории.

        Returns:
            date (str):
                Дата в необходимом формате.
        """
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_nodes(self, node: dict) -> dict:
        """Вывод информации о всех товарах и / или категориях в категории (либо информации о товаре).

        Parameters:
            node (dict):
                Словарь с информацией о товаре / категории, о котором(-й) нужно вывести информацию о потомках.

        Returns:
            nodes (dict):
                Результирующий словарь с информацией о товаре / категории и всех их потомках.
        """
        date = self.convert_date(node["date"])
        result_node = {"date": date, "id": node["id"], "name": node["name"], "parentId": node["parent_id"],
                       "type": node["type"]}
        if node["children"] is not None:
            amount, count = self.calculate_price_for_category(node["id"])
            return result_node | {"children": [self.get_nodes(self.nodes[id]) for id in sorted(node["children"])]} | \
                   {"price": amount // count, "date": self.convert_date(self.calculate_date_for_category(node["id"]))}
        else:
            return result_node | {"price": node["price"], "children": node["children"]}

    def get_sales(self, date: datetime) -> dict:
        """Получение списка товаров, цена которых была обновлена за последние 24 часа от времени переданном в запросе.
        Обновление цены не означает её изменение. Обновления цен удаленных товаров недоступны.

        Parameters:
            date (datetime):
                Дата и время запроса.

        Returns:
            sales (dict):
                Результирующий словарь со списком товаров, цена которых была обновлена за последние 24 часа от date.
        """
        sales = {"items": []}

        for id in self.price_by_id:
            self.price_by_id[id].sort(key=lambda date_and_price: date_and_price[0], reverse=True)
            for node_date, node_price in self.price_by_id[id]:
                difference = date - node_date
                if difference.days <= 1:
                    node = self.nodes[id]
                    result_node = {
                        "id": node["id"],
                        "name": node["name"],
                        "date": self.convert_date(node_date),
                        "parentId": node["parent_id"],
                        "price": node_price,
                        "type": node["type"].value
                    }
                    sales["items"].append(result_node)
                    break

        return sales

    def get_statistic_by_id(self, id: UUID, start_date: datetime = None, end_date: datetime = None) -> dict:
        """Получение статистики (истории обновлений) по цене товара/категории за заданный интервал.
        Статистика по удаленным элементам недоступна. Цена категории - это средняя цена всех её товаров,
        включая товары дочерних категорий. Если категория не содержит товаров цена равна null.
        Можно получить статистику за всё время.

        Parameters:
            id (UUID):
                Уникальный идентификатор товара / категории.

            start_date (datetime | NoneType):
                Дата и время начала интервала, для которого считается статистика.

            end_date (datetime | NoneType):
                Дата и время конца интервала, для которого считается статистика.

        Returns:
            statistic (dict):
                Результирующий словарь со статистикой (истории обновления) по цене.
        """
        statistic = {"items": []}

        if self.nodes[id]["type"].value == "OFFER":
            self.price_by_id[id].sort(key=lambda date_and_price: date_and_price[0], reverse=False)
            for node_date, node_price in self.price_by_id[id]:
                result_date = None
                if start_date and end_date and start_date <= node_date <= end_date:
                    result_date = node_date
                elif start_date and end_date is None and start_date <= node_date:
                    result_date = node_date
                elif end_date and start_date is None and node_date <= end_date:
                    result_date = node_date
                elif start_date is None and end_date is None:
                    result_date = node_date

                if result_date:
                    result_node = {
                        "id": id,
                        "name": self.nodes[id]["name"],
                        "date": result_date,
                        "parentId": self.nodes[id]["parent_id"],
                        "price": node_price,
                        "type": self.nodes[id]["type"]
                    }
                    statistic["items"].append(result_node)
        elif self.nodes[id]["type"].value == "CATEGORY":
            node_date = self.calculate_date_for_category(id)
            amount, count_items = self.calculate_price_for_category(id)
            if count_items == 0:
                node_price = None
            else:
                node_price = amount // count_items

            result_date = None
            if start_date and end_date and start_date <= node_date <= end_date:
                result_date = node_date
            elif start_date and end_date is None and start_date <= node_date:
                result_date = node_date
            elif end_date and start_date is None and node_date <= end_date:
                result_date = node_date
            elif start_date is None and end_date is None:
                result_date = node_date

            if result_date:
                result_node = {
                    "id": id,
                    "name": self.nodes[id]["name"],
                    "date": result_date,
                    "parentId": self.nodes[id]["parent_id"],
                    "price": node_price,
                    "type": self.nodes[id]["type"]
                }
                statistic["items"].append(result_node)

        return statistic
