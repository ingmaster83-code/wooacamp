require 'json'

module Jekyll
  class CampPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      camps = load_json(site, '_rawdata/camps.json')
      return if camps.empty?

      Jekyll.logger.info "CampGenerator:", "#{camps.size}개 캠핑장 페이지 생성 중..."

      camps.each do |camp|
        next if camp['slug'].to_s.strip.empty?
        site.pages << CampPage.new(site, camp)
      end

      # 검색 인덱스 생성
      site.pages << SearchIndexPage.new(site, camps)

      Jekyll.logger.info "CampGenerator:", "완료 (#{camps.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "CampGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class CampPage < Page
    def initialize(site, camp)
      @site = site
      @base = site.source
      @dir  = "camp/#{camp['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'camp.html')
      self.data.merge!(camp)
      self.data['layout']      = 'camp'
      self.data['title']       = build_title(camp)
      self.data['description'] = build_desc(camp)
    end

    private

    def build_title(camp)
      name = camp['facltNm'] || ''
      loc  = [camp['doNm'], camp['sigunguNm']].compact.join(' ')
      "#{name} 위치 시설 예약 | 우아캠프"
    end

    def build_desc(camp)
      return camp['seoDescription'] if camp['seoDescription'].to_s.length > 10
      name   = camp['facltNm'] || ''
      loc    = [camp['doNm'], camp['sigunguNm']].compact.join(' ')
      induty = camp['induty'] || ''
      intro  = (camp['lineIntro'] || '').strip[0, 60]
      desc   = "#{loc} #{name} #{induty} 캠핑장. 위치, 시설, 예약 정보를 확인하세요."
      desc  += " #{intro}" if intro.length > 5
      desc[0, 155]
    end
  end

  class SearchIndexPage < Page
    def initialize(site, camps)
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      index = camps.map do |c|
        {
          'contentId'     => c['contentId'],
          'slug'          => c['slug'],
          'facltNm'       => c['facltNm'],
          'induty'        => c['induty'],
          'doNm'          => c['doNm'],
          'sigunguNm'     => c['sigunguNm'],
          'addr1'         => c['addr1'],
          'firstImageUrl' => c['firstImageUrl'],
          'sbrsCl'        => c['sbrsCl'],
          'animalCmgCl'   => c['animalCmgCl'],
          'resveCl'       => c['resveCl'],
          'mapX'          => c['mapX'],
          'mapY'          => c['mapY'],
          'lineIntro'     => (c['lineIntro'] || '')[0, 80],
        }
      end

      self.content = index.to_json
    end

    def output   = self.content
    def render(layouts, registers); end
  end
end
