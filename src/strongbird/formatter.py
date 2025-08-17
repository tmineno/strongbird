"""Output formatting module for Strongbird."""

import re
from typing import Any, Dict


def format_output(result: Dict[str, Any], format_type: str, with_metadata: bool) -> str:
    """
    Format extraction result for output.

    Args:
        result: Extraction result dictionary
        format_type: Output format type
        with_metadata: Whether to include metadata

    Returns:
        Formatted string output
    """
    content = result.get("content", "")
    metadata = result.get("metadata", {})
    image_mappings = result.get("image_mappings", {})

    # Replace image URLs with local paths if we have mappings
    if image_mappings and format_type.lower() == "markdown":
        content = replace_image_urls(content, image_mappings)

    # For JSON and XML, content already includes metadata if requested
    if format_type.lower() in ["json", "xml", "csv"]:
        return content

    # For markdown and text, we may need to prepend metadata
    if format_type.lower() == "markdown":
        return format_as_markdown(content, metadata, with_metadata)
    else:  # text
        return format_as_text(content, metadata, with_metadata)


def format_as_markdown(
    content: str, metadata: Dict[str, Any], with_metadata: bool
) -> str:
    """Format output as Markdown with optional metadata."""
    if not with_metadata or not metadata:
        return content

    output = []

    # Add metadata as YAML frontmatter
    output.append("---")
    if "title" in metadata:
        output.append(f"title: {metadata['title']}")
    if "author" in metadata:
        output.append(f"author: {metadata['author']}")
    if "date" in metadata:
        output.append(f"date: {metadata['date']}")
    if "url" in metadata:
        output.append(f"url: {metadata['url']}")
    if "sitename" in metadata:
        output.append(f"site: {metadata['sitename']}")
    if "description" in metadata:
        output.append(f"description: {metadata['description']}")
    if "language" in metadata:
        output.append(f"language: {metadata['language']}")
    if "categories" in metadata and metadata["categories"]:
        output.append(f"categories: [{', '.join(metadata['categories'])}]")
    if "tags" in metadata and metadata["tags"]:
        output.append(f"tags: [{', '.join(metadata['tags'])}]")
    output.append("---")
    output.append("")

    # Add content
    output.append(content)

    return "\n".join(output)


def format_as_text(content: str, metadata: Dict[str, Any], with_metadata: bool) -> str:
    """Format output as plain text with optional metadata."""
    if not with_metadata or not metadata:
        return content

    output = []

    # Add metadata header
    output.append("=" * 60)
    if "title" in metadata:
        output.append(f"Title: {metadata['title']}")
    if "author" in metadata:
        output.append(f"Author: {metadata['author']}")
    if "date" in metadata:
        output.append(f"Date: {metadata['date']}")
    if "url" in metadata:
        output.append(f"URL: {metadata['url']}")
    if "sitename" in metadata:
        output.append(f"Site: {metadata['sitename']}")
    if "description" in metadata:
        output.append(f"Description: {metadata['description']}")
    if "language" in metadata:
        output.append(f"Language: {metadata['language']}")
    if "categories" in metadata and metadata["categories"]:
        output.append(f"Categories: {', '.join(metadata['categories'])}")
    if "tags" in metadata and metadata["tags"]:
        output.append(f"Tags: {', '.join(metadata['tags'])}")
    output.append("=" * 60)
    output.append("")

    # Add content
    output.append(content)

    return "\n".join(output)


def replace_image_urls(content: str, image_mappings: Dict[str, str]) -> str:
    """
    Replace image URLs in Markdown content with local paths.

    Args:
        content: Markdown content
        image_mappings: Dictionary mapping original URLs to local paths

    Returns:
        Content with replaced image URLs
    """

    # Replace Markdown image syntax: ![alt](url)
    def replace_markdown_image(match):
        alt_text = match.group(1)
        url = match.group(2)
        title = match.group(3) if match.group(3) else ""

        # Check if we have a local path for this URL
        local_path = image_mappings.get(url)
        if local_path:
            if title:
                return f"![{alt_text}]({local_path}{title})"
            else:
                return f"![{alt_text}]({local_path})"
        return match.group(0)  # Return original if no mapping

    # Pattern for Markdown images: ![alt](url "optional title")
    markdown_pattern = r'!\[([^\]]*)\]\(([^)]+?)(\s+"[^"]*")?\)'
    content = re.sub(markdown_pattern, replace_markdown_image, content)

    # Replace HTML img tags that might be in the content
    def replace_html_image(match):
        full_tag = match.group(0)
        src_match = re.search(r'src=["\']([^"\']+)["\']', full_tag)
        if src_match:
            src_url = src_match.group(1)
            local_path = image_mappings.get(src_url)
            if local_path:
                return full_tag.replace(src_url, local_path)
        return full_tag

    # Pattern for HTML img tags
    html_pattern = r"<img[^>]+>"
    content = re.sub(html_pattern, replace_html_image, content)

    return content
