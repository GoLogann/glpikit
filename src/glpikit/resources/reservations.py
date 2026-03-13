"""Reservations resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ReservationsResource(GenericItemtypeResource):
    itemtype = "Reservation"


class AsyncReservationsResource(AsyncGenericItemtypeResource):
    itemtype = "Reservation"
