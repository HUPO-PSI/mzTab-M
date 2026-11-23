# Asciidoctor extension for the DocBook build that feeds the DOCX (via pandoc).
#
# DocBook leaves section/caption numbering and cross-reference text to its
# XSL stylesheets, which pandoc does not apply. This extension writes the
# numbers Asciidoctor computes (the same ones the PDF and HTML show) into the
# DocBook output:
#   - numbered section titles get their number prefix ("7.2. Metadata Section"),
#   - figure/table/listing/example titles get their caption ("Figure 1. ..."),
#   - cross references without text get the xrefstyle text ("Section 7.2").
#
# Usage: asciidoctor -b docbook -r ./docx-theme/docbook-numbering.rb doc.adoc
require 'asciidoctor'
require 'asciidoctor/extensions'

module MzTabDocx
  class NumberTitles < Asciidoctor::Extensions::TreeProcessor
    CAPTIONED = [:image, :table, :listing, :example].freeze

    def process doc
      return unless doc.backend == 'docbook5'
      levels = (doc.attr 'sectnumlevels', 3).to_i
      # Collect first, then rename: changing titles while traversing is fine,
      # but sectnum must be read before any title changes for clarity.
      sections = doc.find_by(context: :section).select do |sect|
        sect.numbered && sect.level <= levels && sect.sectname != 'part'
      end
      sections.each do |sect|
        sect.title = %(#{sect.sectnum} #{raw_title sect})
      end
      doc.find_by {|b| (CAPTIONED.include? b.context) && b.title? && b.caption }.each do |block|
        block.title = %(#{block.caption}#{raw_title block})
        block.caption = nil
      end
      nil
    end

    private

    def raw_title node
      node.instance_variable_get :@title
    end
  end

  class DocBookConverter < (Asciidoctor::Converter.for 'docbook5')
    register_for 'docbook5'

    # Resolve <xref/> without text to the text the PDF/HTML show, e.g.
    # "Chapter 2" or "Section 7.2" for xrefstyle=short.
    def convert_inline_anchor node
      if node.type == :xref && !node.text && !node.attributes['path'] &&
          (refid = node.attributes['refid']) && !refid.empty? &&
          (ref = node.document.catalog[:refs][refid]) &&
          (text = ref.xreftext node.attr('xrefstyle', nil, true)) && !text.empty?
        return %(<link linkend="#{refid}">#{text}</link>)
      end
      super
    end
  end
end

Asciidoctor::Extensions.register do
  tree_processor MzTabDocx::NumberTitles
end
