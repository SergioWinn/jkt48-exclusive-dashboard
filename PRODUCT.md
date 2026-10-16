# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are JKT48 fans looking for available tickets. Statistics support that task.

## Product Purpose

Help fans choose an Exclusive event, date, session, and member, check ticket availability, and open the existing purchase link.

## Operating Context

The existing Streamlit dashboard monitors the JKT48 public API and falls back to saved snapshots when live data is unavailable. Users can filter by category, event, member, date, and availability. Admins can import snapshots and copy report images.

## Capabilities and Constraints

- Preserve all existing functions, data, purchase destinations, and admin restrictions.
- Keep member, generation, and team statistics available as supporting information.
- Keep the data-source readout compact, showing status and update time.
- Closed ticket cards display CLOSED without historical quantities.
- Do not introduce the rejected wording Last count, Count unknown, or Stock may be outdated.
- Preserve keyboard navigation, responsive layouts, and the existing polling and recovery behavior.

## Brand Commitments

Preserve the existing product name and logo. The user requested a full visual replacement and pinned the approximate layout of https://dashboard-exclusive.streamlit.app/: simple masthead, filter bar, event title/date, and vertical member cards grouped by session. Improve usability rather than reproducing its oversized data status or cramped mobile heading.

## Evidence on Hand

- Existing implementation in app.py, core/, and ui/.
- Product and workflow documentation in README.md.
- Existing logos in assets/ and member metadata in data/.
- Existing tests in tests/.
- No additional commercial claims, endorsements, or sales promises were supplied.

## Product Principles

- Make available tickets easy to find and compare.
- Give event, date, member, and availability priority over statistics.
- Distinguish live, partial, saved, unavailable, and closed states honestly and concisely.
- Preserve a working path through filters, purchase links, and data recovery on mobile and desktop.
