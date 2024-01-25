#!/usr/bin/env python3
"""
A simple-as-possible script to generate an RSS feed out of the latest 10 markdown files
in a given directory.

We depend on Markdown from Daring Fireball being on the $PATH:
https://daringfireball.net/projects/markdown/
We also depend on `date`:
https://www.gnu.org/software/coreutils/manual/html_node/date-invocation.html
"""
import datetime
import math
import os
import pathlib
import subprocess
import sys
import time
import typing
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, ElementTree

DATETIME_FORMAT = "%a, %d %b %Y %X %z"
TZ_INFO = datetime.timezone(
    datetime.timedelta(seconds=time.localtime().tm_gmtoff)
)  # whew


class InvalidMarkdownFile(Exception):
    """Exception raised when a file cannot be parsed as a MarkdownFile."""


class MarkdownFile:
    """A wrapper for a file containing Markdown.

    :param stream: a file-like object that contains the Markdown text.
    """

    def __init__(self, stream: typing.TextIO):
        title_line = stream.readline()
        _ = stream.readline()
        date_line = stream.readline()
        stream.seek(0)

        if not title_line.startswith("# "):
            raise InvalidMarkdownFile("Missing title header")

        if not date_line.startswith("## "):
            raise InvalidMarkdownFile("Missing date header")

        self.stream = stream
        self.title = title_line.lstrip("#").strip()

        try:
            date = datetime.datetime.fromisoformat(date_line.lstrip("#").strip())
        except ValueError:
            raise InvalidMarkdownFile("Date header is not a valid ISO date")

        self.pub_date = date.combine(date.date(), date.time(), TZ_INFO)

    @property
    def content(self) -> str:
        """The contents of the backing file-like object, converted to Markdown."""
        try:
            completed_process = subprocess.run(
                ["markdown", "--html4tags"],
                input=self.stream.read(),
                capture_output=True,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # This is pretty rare - all text can be converted to markdown, so it's not a parsing
            # error.
            raise InvalidMarkdownFile(f"Could not convert to Markdown {e.stderr}")

        return completed_process.stdout

    def close(self) -> None:
        """Closes the backing file-like object."""
        return self.stream.close()


class RssElementTree(ElementTree):
    """An XML ElementTree representing an RSS feed.

    :param title: The title of the site the RSS feed represents.
    :param description: The description of the RSS feed.
    :param url: The URL of the site the RSS feed represents.
    :param pub_date: The publication date of the RSS feed. If `None`, it is generated from local
        time. If provided, it is not validated.
    """

    def __init__(
        self, title: str, description: str, url: str, pub_date: str | None = None
    ):
        if pub_date is None:
            pub_date = generate_pub_date()

        element = Element(
            "rss",
            attrib={"version": "2.0", "xlmns:atom": "http://www.w3.org/2005/Atom"},
        )

        channel = ET.SubElement(element, "channel")
        ET.SubElement(channel, "title").text = title
        ET.SubElement(channel, "description").text = description
        ET.SubElement(channel, "link").text = url
        channel.append(
            Element(
                "atom:link",
                attrib={
                    "href": f"{url}feed.xml",
                    "rel": "self",
                    "type": "application/rss+xml",
                },
            )
        )
        ET.SubElement(channel, "pubDate").text = pub_date
        ET.SubElement(channel, "lastBuildDate").text = pub_date
        ET.SubElement(channel, "generator").text = "simple-site"

        element.append(channel)

        self.channel = channel

        return super().__init__(element=element)

    def append_item(self, md_file: MarkdownFile) -> None:
        """Adds `md_file` to the list of RSS items."""
        item = Element("item")
        ET.SubElement(item, "title").text = md_file.title
        ET.SubElement(item, "description").text = md_file.content
        ET.SubElement(item, "pubDate").text = md_file.pub_date.strftime(DATETIME_FORMAT)

        self.channel.append(item)


def collect_md_files(
    directory: pathlib.Path, max_files: int | None
) -> tuple[dict[pathlib.Path, MarkdownFile], list[str]]:
    """Collects Markdown files in `directory`, searching recursively.

    Files are sorted on two fields: first, their publication date, derived from the second line,
    then by their title, derived from the first line. If a file is lacking either of these, it is
    omitted with a warning.

    :param directory: the directory to recursively search for Markdown files.
    :param max_files: the maximum number of Markdown files to include. Files are sorted on two
        fields: first, their publication date, derived from the second line, then by their title
    """
    md_files: list[tuple[pathlib.Path, MarkdownFile]] = []
    skipped = []
    stack = [directory]

    target = max_files if max_files else math.inf

    while stack and len(md_files) < target:
        current = stack.pop()

        for dir_entry in os.scandir(current):
            path = pathlib.Path(dir_entry.path)

            if dir_entry.is_dir():
                stack.append(path)
                continue

            try:
                fp = open(path)
                md_files.append((path, MarkdownFile(fp)))
            except InvalidMarkdownFile as e:
                skipped.append(f"Skipped {path}: {e}")

            if len(md_files) >= target:
                break

    md_files.sort()

    return dict(md_files), skipped


def generate_pub_date() -> str:
    """Generates a properly-formatted publication date based on local time."""
    now = datetime.datetime.now()
    now = now.combine(now.date(), now.time(), TZ_INFO)

    return now.strftime(DATETIME_FORMAT)


def main(
    directory: pathlib.Path,
    title: str,
    description: str,
    url: str,
    max_files: int | None = None,
) -> tuple[RssElementTree | None, list[pathlib.Path], list[str]]:
    """Collects Markdown files in `directory`, generating and outputting an RSS feed.
    Markdown files are identified by ".md" endings only.

    :param directory: the directory to recursively search for Markdown files.
    :param title: the title for the RSS feed.
    :param description: the description of the RSS feed.
    :param url: the URL of the site the RSS feed represents.
    :param max_files: the maximum number of Markdown files to include in the RSS feed. Files are
        sorted on two fields: first, their publication date, derived from the second line, then by
        their title.

    :returns: the completed RSS feed
    """
    md_files, errors = collect_md_files(directory, max_files)

    if not md_files:
        return (
            None,
            [],
            [
                f'No markdown files found in {directory} (we are dumb and only check for ".md" file'
                "extensions)"
            ],
        )

    rss_tree = RssElementTree(title, description, url)
    included_files = []

    for path, md_file in md_files.items():
        try:
            rss_tree.append_item(md_file)
            included_files.append(path)
        except InvalidMarkdownFile as e:
            errors.append(f"Skipped {path}: {e}")

        md_file.close()

    return rss_tree, included_files, errors


if __name__ == "__main__":
    directory = pathlib.Path("./markdown/")

    rss_tree, included, errors = main(
        directory,
        "Perfect5th, 2.0",
        'I make-a the software go "beep-boop"',
        "https://mitchellburton.ca/blog/",
    )

    for path in included:
        print(f"Processed file: {path}")

    for error in errors:
        print(error, file=sys.stderr)

    if rss_tree is not None:
        print()
        rss_tree.write(sys.stdout, encoding="unicode", xml_declaration=True)
        rss_tree.write("feed.xml", encoding="unicode", xml_declaration=True)
        print()
