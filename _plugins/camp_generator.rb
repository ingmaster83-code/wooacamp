require 'json'

module Jekyll
  # 우아동네(wooatown) 지역 페이지 slug / wooacamp 자체 /region/ 폴더명 (공식 시도명 → 짧은 한글 시도명)
  WOOATOWN_SIDO = {
    '서울특별시' => '서울', '부산광역시' => '부산', '대구광역시' => '대구',
    '인천광역시' => '인천', '광주광역시' => '광주', '대전광역시' => '대전',
    '울산광역시' => '울산', '세종특별자치시' => '세종', '경기도' => '경기',
    '강원특별자치도' => '강원', '강원도' => '강원',
    '충청북도' => '충북', '충청남도' => '충남',
    '전북특별자치도' => '전북', '전라북도' => '전북', '전라남도' => '전남',
    '경상북도' => '경북', '경상남도' => '경남',
    '제주특별자치도' => '제주', '제주도' => '제주',
  }.freeze

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
      self.data['doShort']     = WOOATOWN_SIDO[camp['doNm']] || camp['doNm']
    end

    private

    # 검색결과 title이 영문 병기 괄호 때문에 길어져서 "위치 시설 예약"이 잘려나가는 문제 방지.
    # 예: "럭스피아 캠핑장(LUXPIA CAMPGROUND)" -> "럭스피아 캠핑장"
    def display_name(faclt_nm)
      name = (faclt_nm || '').to_s
      stripped = name.sub(/\s*\(.*\)\s*\z/, '').strip
      stripped.empty? ? name : stripped
    end

    def build_title(camp)
      name = display_name(camp['facltNm'])
      loc  = [camp['doNm'], camp['sigunguNm']].compact.join(' ')
      "#{name} #{loc} 위치 시설 예약"
    end

    def build_desc(camp)
      return camp['seoDescription'] if camp['seoDescription'].to_s.length > 10
      name   = display_name(camp['facltNm'])
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
          'posblFcltyCl'  => c['posblFcltyCl'],
          'themaEnvrnCl'  => c['themaEnvrnCl'],
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
